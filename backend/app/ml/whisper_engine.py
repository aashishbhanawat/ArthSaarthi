import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import requests

from app.ml.model_manager import model_manager

logger = logging.getLogger(__name__)
logging.getLogger("faster_whisper").setLevel(logging.INFO)

# Decoder bias prompt for Indian earnings calls (prior weights for financial terms)
FINANCIAL_WHISPER_PROMPT = (
    "Indian corporate earnings conference call transcript. "
    "Terms: crores, lakhs, EBITDA, PAT, YoY, QoQ, basis points, bps, "
    "top line, bottom line, order book, capex, working capital, guidance, "
    "railways, RVNL, Vande Bharat, metro, electrification, margin, realization, "
    "revenue from operations, quarterly results, execution."
)

# Post-ASR phonetic corrections for common Whisper distortions on Indian accents
ASR_CORRECTIONS = [
    # Indian numbering & crore phonetics: "171 corona" -> "171 crores", "9.6 store" -> "9.6 crores", "24,801 crew" -> "24,801 crores", "25.2 per hour" -> "25.2 crore"
    (r"(\b\d+(?:,\d+)*(?:\.\d+)?)\s*(?:corona|coronas|store|stores|grower|crew|crews|through)\b", r"\1 crores"),
    (r"(\b\d+(?:,\d+)*(?:\.\d+)?)\s*(?:per\s+hour|per\s+or)\b", r"\1 crore"),
    (r"\bper\s+row\b", "per crore"),
    (r"\bper\s+city\s+utilization\b", "capacity utilization"),
    (r"\bstop\s+line\b", "top line"),
    (r"\b(?:crew|queue)\s*(?:to|two)\s*(FY\s*\d{2,4}|\d{4})\b", r"Q2 \1"),
    (r"\bcrew\s+by\s+(?:around\s+)?(\d+(?:\.\d+)?%?)", r"grew by \1"),
    (r"\bto\s+go\s+by\s+(?:around\s+)?(\d+%)", r"to grow by around \1"),
    (r"\bselected\s+to\s+increase\b", "expected to increase"),
    (r"\bcracking\s+closely\b", "tracking closely"),
    (r"\bmental\s+margin\b", "maintain margin"),
    # Financial acronyms & phrases: "the fact of 6,447" -> "the PAT of 6,447", "back of another" -> "PAT of NRL", "part was 46 crores" -> "PAT was 46 crores"
    (r"\b(?:the\s+)?fact\s+of\s+(\d+(?:,\d+)*(?:\.\d+)?)", r"the PAT of \1"),
    (r"\bthe\s+fact\s+for\b", "the PAT for"),
    (r"\bhalf\s+yearly\s+back\b", "half yearly PAT"),
    (r"\b3D\s+back\b", "PAT"),
    (r"\bback\s+of\s+another\b", "PAT of NRL"),
    (r"\b(?:cash\s+)?back\s+of\s+(?:rupees\s+|INR\s+|₹\s*)?(\d+(?:,\d+)*(?:\.\d+)?\s*(?:crores?|cr|lakhs?))", r"cash PAT of rupees \1"),
    (r"\bpart\s+was\s+(\d+(?:,\d+)*(?:\.\d+)?\s*(?:crores?|cr|lakhs?))", r"PAT was \1"),
    (r"\b(?:conesoly\s+rated|consolidate\s+rated|conesoly\s+date|consolidated)\s+fact\b", "consolidated PAT"),
    (r"\bfact\s+goes\s+to\b", "PAT goes to"),
    (r"\boperating\s+revenue\s+of\s+an\s+hour\s+loop\b", "operating revenue of NRL"),
    (r"\ban\s+hour\s+loop\b", "NRL"),
    # Collapse stuttered duplicate words ("employee employee" -> "employee")
    (r"\b([a-zA-Z]+)\s+\1\b", r"\1"),
]


def normalize_whisper_transcript(text: str) -> str:
    """Normalizes Whisper transcription text by correcting common Indian financial mishearings."""
    for pattern, replacement in ASR_CORRECTIONS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


class WhisperEngine:
    """
    Edge Speech-to-Text Transcriber for earnings conference calls and audio podcasts.
    Powered by faster-whisper (CTranslate2 INT8 quantized on-device inference).
    """

    MODEL_ID = "whisper_tiny_en"
    MODEL_SIZE = "tiny.en"

    def __init__(self):
        self._model = None

    @property
    def is_available(self) -> bool:
        """Returns True if faster-whisper runtime is installed."""
        if hasattr(self, "_is_available") and self._is_available is not None:
            return self._is_available
        try:
            import faster_whisper  # noqa: F401
            return True
        except ImportError:
            return False

    @is_available.setter
    def is_available(self, value: bool) -> None:
        self._is_available = value

    @is_available.deleter
    def is_available(self) -> None:
        if hasattr(self, "_is_available"):
            del self._is_available

    def _get_model(self):
        """Lazy loads faster-whisper CTranslate2 model on CPU with INT8 quantization."""
        if self._model is None:
            from faster_whisper import WhisperModel
            download_root = str(model_manager.models_dir / "whisper")
            logger.info("Initializing faster-whisper '%s' (compute_type=int8) at %s", self.MODEL_SIZE, download_root)
            self._model = WhisperModel(
                self.MODEL_SIZE,
                device="cpu",
                compute_type="int8",
                download_root=download_root,
            )
        return self._model

    def get_status(self) -> dict:
        """Returns model status and readiness for speech-to-text transcription."""
        info = model_manager.get_model_status(self.MODEL_ID)
        return {
            "model_id": self.MODEL_ID,
            "engine": "faster-whisper",
            "status": info.status,
            "is_available": self.is_available,
            "size_mb": info.size_mb,
            "filename": info.filename,
            "model_size": self.MODEL_SIZE,
        }

    def transcribe_audio_file(self, audio_path: str | Path, max_bytes: int = 60 * 1024 * 1024) -> str:
        """
        Transcribes audio file or remote audio URL to text using faster-whisper.
        """
        if not self.is_available:
            raise RuntimeError(
                "faster-whisper library is not installed. "
                "Please paste the official conference call transcript or upload the BSE filing PDF directly."
            )

        audio_str = str(audio_path)
        if audio_str.startswith(("http://", "https://")):
            return self._download_and_transcribe(audio_str, max_bytes=max_bytes)

        local_path = Path(audio_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Audio file not found: {local_path}")

        try:
            return self._transcribe_with_model(local_path)
        except Exception as e:
            logger.error("Audio transcription failed: %s", e)
            raise RuntimeError(f"Transcription error: {str(e)}")

    def _download_and_transcribe(self, url: str, max_bytes: int = 60 * 1024 * 1024) -> str:
        """
        Streams and downloads remote audio into a temporary local file with retries,
        then invokes transcription.
        """
        import time

        suffix = ".m4a" if ".m4a" in url.lower() else ".mp3"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        max_attempts = 3
        last_error = None

        try:
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info("Downloading remote concall audio (attempt %d/%d) from %s", attempt, max_attempts, url)
                    with requests.get(url, stream=True, timeout=120, headers=headers) as resp:
                        resp.raise_for_status()
                        with open(tmp_path, "wb") as f:
                            for chunk in resp.iter_content(chunk_size=1048576):
                                if chunk:
                                    f.write(chunk)
                    last_error = None
                    break
                except Exception as e:
                    last_error = e
                    logger.warning("Download attempt %d/%d failed for %s: %s", attempt, max_attempts, url, e)
                    if attempt < max_attempts:
                        time.sleep(1.5 * attempt)

            if last_error is not None:
                err_str = str(last_error)
                if "NameResolutionError" in err_str or "Failed to resolve" in err_str or "Errno -2" in err_str:
                    clean_msg = "Temporary DNS/network resolution error while contacting audio storage. Please retry."
                else:
                    clean_msg = f"Network error downloading audio: {err_str}"
                logger.error("Failed to stream remote audio %s after %d attempts: %s", url, max_attempts, clean_msg)
                raise RuntimeError(clean_msg)

            return self._transcribe_with_model(tmp_path)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    def _transcribe_with_model(self, audio_path: str | Path) -> str:
        """
        Internal transcription runner using faster-whisper.
        Decodes audio directly via bundled PyAV (no system ffmpeg binary required).
        """
        path_str = str(audio_path)
        if not os.path.exists(path_str):
            raise FileNotFoundError(f"Audio file not found: {path_str}")

        file_size = os.path.getsize(path_str)
        if file_size == 0:
            return ""

        model = self._get_model()
        logger.info("Starting faster-whisper transcription on %s (%0.1f MB)", path_str, file_size / (1024 * 1024))
        segments, info = model.transcribe(
            path_str,
            beam_size=1,
            language="en",
            condition_on_previous_text=False,
            vad_filter=True,
            initial_prompt=FINANCIAL_WHISPER_PROMPT,
        )

        transcript_segments = []
        for s in segments:
            text = s.text.strip()
            if text:
                transcript_segments.append(normalize_whisper_transcript(text))

        full_transcript = " ".join(transcript_segments).strip()
        logger.info(
            "Completed faster-whisper transcription: %d segments, %d chars (detected lang: %s)",
            len(transcript_segments),
            len(full_transcript),
            info.language,
        )
        return full_transcript


whisper_engine = WhisperEngine()

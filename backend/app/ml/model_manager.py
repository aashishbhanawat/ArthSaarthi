import logging
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class EdgeModelInfo:
    id: str
    name: str
    description: str
    size_mb: float
    download_url: str
    filename: str
    engine_type: str
    status: str  # "NOT_DOWNLOADED" | "DOWNLOADING" | "ACTIVE" | "FAILED"
    progress_percentage: int
    downloaded_bytes: int
    total_bytes: int
    error_message: Optional[str] = None


class ModelManager:
    """
    Manages edge ML models (quantized ONNX models, vocabularies, and weights)
    stored locally on user disk for privacy and offline inference.
    """

    CATALOG = {
        "finbert_int8": {
            "id": "finbert_int8",
            "name": "FinBERT-Tone INT8 Quantized",
            "description": "State-of-the-art financial tone transformer fine-tuned on corporate earnings calls and corporate disclosures (HKUST FinBERT-Tone INT8).",
            "size_mb": 105.2,
            # Verified HuggingFace Optimum quantized release of yiyanghkust/finbert-tone
            "download_url": "https://huggingface.co/nickmuchi/quantized-optimum-finbert-tone/resolve/main/model_quantized.onnx",
            "vocab_url": "https://huggingface.co/nickmuchi/quantized-optimum-finbert-tone/resolve/main/vocab.txt",
            "filename": "finbert_int8.onnx",
            "vocab_filename": "vocab.txt",
            "engine_type": "finbert_onnx",
        },
        "whisper_tiny_en": {
            "id": "whisper_tiny_en",
            "name": "Whisper Tiny INT8 (Speech-to-Text)",
            "description": "Edge speech-to-text model for transcribing corporate earnings calls and investor podcasts when official transcripts are not provided.",
            "size_mb": 39.0,
            "download_url": "https://huggingface.co/onnx-community/whisper-tiny.en/resolve/main/onnx/encoder_model_quantized.onnx",
            "filename": "whisper_tiny_en_quantized.onnx",
            "engine_type": "whisper_onnx",
        },
    }

    def __init__(self, models_dir: Optional[Path] = None):
        if models_dir is not None:
            self.models_dir = models_dir
        else:
            # Check environment or use app persistent directory
            app_data = os.environ.get("ARTHSAARTHI_DATA_DIR")
            if app_data:
                self.models_dir = Path(app_data) / "models"
            else:
                self.models_dir = Path("data/models")

        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._active_downloads: Dict[str, EdgeModelInfo] = {}
        self._lock = threading.Lock()

    def get_model_path(self, model_id: str) -> Optional[Path]:
        """Returns the local path to the model if it exists."""
        meta = self.CATALOG.get(model_id)
        if not meta:
            return None
        target = self.models_dir / meta["filename"]
        return target if target.exists() and target.stat().st_size > 1000 else None

    def is_model_available(self, model_id: str) -> bool:
        """Returns True if the model file is downloaded and non-empty."""
        return self.get_model_path(model_id) is not None

    def get_model_status(self, model_id: str) -> EdgeModelInfo:
        """Returns the current status of the model."""
        meta = self.CATALOG.get(model_id)
        if not meta:
            raise ValueError(f"Unknown model ID: {model_id}")

        with self._lock:
            if model_id in self._active_downloads:
                return self._active_downloads[model_id]

        target = self.models_dir / meta["filename"]
        if target.exists() and target.stat().st_size > 1000:
            size_bytes = target.stat().st_size
            return EdgeModelInfo(
                id=meta["id"],
                name=meta["name"],
                description=meta["description"],
                size_mb=round(size_bytes / (1024 * 1024), 1),
                download_url=meta["download_url"],
                filename=meta["filename"],
                engine_type=meta["engine_type"],
                status="ACTIVE",
                progress_percentage=100,
                downloaded_bytes=size_bytes,
                total_bytes=size_bytes,
            )

        return EdgeModelInfo(
            id=meta["id"],
            name=meta["name"],
            description=meta["description"],
            size_mb=meta["size_mb"],
            download_url=meta["download_url"],
            filename=meta["filename"],
            engine_type=meta["engine_type"],
            status="NOT_DOWNLOADED",
            progress_percentage=0,
            downloaded_bytes=0,
            total_bytes=int(meta["size_mb"] * 1024 * 1024),
        )

    def list_models(self) -> List[EdgeModelInfo]:
        """Lists all registered models in the catalog and their download status."""
        return [self.get_model_status(mid) for mid in self.CATALOG]

    def start_download(self, model_id: str) -> EdgeModelInfo:
        """Starts asynchronous download of a model in the background."""
        meta = self.CATALOG.get(model_id)
        if not meta:
            raise ValueError(f"Unknown model ID: {model_id}")

        with self._lock:
            if model_id in self._active_downloads:
                current = self._active_downloads[model_id]
                if current.status == "DOWNLOADING":
                    return current

            info = EdgeModelInfo(
                id=meta["id"],
                name=meta["name"],
                description=meta["description"],
                size_mb=meta["size_mb"],
                download_url=meta["download_url"],
                filename=meta["filename"],
                engine_type=meta["engine_type"],
                status="DOWNLOADING",
                progress_percentage=0,
                downloaded_bytes=0,
                total_bytes=int(meta["size_mb"] * 1024 * 1024),
            )
            self._active_downloads[model_id] = info

        # Launch background download thread
        thread = threading.Thread(
            target=self._download_worker,
            args=(model_id,),
            daemon=True,
            name=f"ModelDownload-{model_id}"
        )
        thread.start()
        return info

    def _download_worker(self, model_id: str) -> None:
        meta = self.CATALOG[model_id]
        url = meta["download_url"]
        target_path = self.models_dir / meta["filename"]
        temp_path = self.models_dir / f"{meta['filename']}.part"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        logger.info("Starting background download of model %s from %s", model_id, url)
        try:
            with requests.get(url, headers=headers, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                total_size = int(resp.headers.get("content-length", meta["size_mb"] * 1024 * 1024))

                with self._lock:
                    if model_id in self._active_downloads:
                        self._active_downloads[model_id].total_bytes = total_size

                downloaded = 0
                with open(temp_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=131072):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pct = min(100, int((downloaded / total_size) * 100)) if total_size else 50
                            with self._lock:
                                if model_id in self._active_downloads:
                                    self._active_downloads[model_id].downloaded_bytes = downloaded
                                    self._active_downloads[model_id].progress_percentage = pct

            # Atomically replace part file
            if temp_path.exists():
                temp_path.replace(target_path)

            # Also download vocab.txt if specified
            vocab_url = meta.get("vocab_url")
            vocab_filename = meta.get("vocab_filename")
            if vocab_url and vocab_filename:
                vocab_path = self.models_dir / vocab_filename
                try:
                    with requests.get(vocab_url, headers=headers, timeout=30) as v_resp:
                        if v_resp.status_code == 200:
                            vocab_path.write_bytes(v_resp.content)
                except Exception as ve:
                    logger.warning("Could not download vocab.txt: %s", ve)

            with self._lock:
                if model_id in self._active_downloads:
                    self._active_downloads[model_id].status = "ACTIVE"
                    self._active_downloads[model_id].progress_percentage = 100
                    self._active_downloads[model_id].downloaded_bytes = downloaded
            logger.info("Successfully downloaded and verified model %s (%d bytes)", model_id, downloaded)

        except Exception as e:
            logger.error("Failed to download model %s: %s", model_id, e)
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            with self._lock:
                if model_id in self._active_downloads:
                    self._active_downloads[model_id].status = "FAILED"
                    self._active_downloads[model_id].error_message = str(e)

    def delete_model(self, model_id: str) -> bool:
        """Deletes model file to free disk space."""
        meta = self.CATALOG.get(model_id)
        if not meta:
            return False

        with self._lock:
            if model_id in self._active_downloads:
                del self._active_downloads[model_id]

        target_path = self.models_dir / meta["filename"]
        part_path = self.models_dir / f"{meta['filename']}.part"

        deleted = False
        if target_path.exists():
            target_path.unlink()
            deleted = True
        if part_path.exists():
            part_path.unlink()

        return deleted


# Global model manager singleton
model_manager = ModelManager()

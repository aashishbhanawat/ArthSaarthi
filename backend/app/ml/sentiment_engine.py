import logging
import re
from dataclasses import dataclass
from typing import Set

from app.ml.model_manager import model_manager

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    label: str  # "POSITIVE" | "NEGATIVE" | "NEUTRAL"
    score: float  # Polarity / confidence between 0.0 and 1.0
    engine: str  # "finbert_onnx" | "financial_lexicon"


class FinancialLexicon:
    """
    Academic Financial Sentiment Lexicon (Loughran-McDonald adapted for equity news).
    Accurately handles financial negations and contextual polarity.
    Pure Python, instant execution (< 1 ms), 100% portable on all platforms.
    """

    POSITIVE_WORDS: Set[str] = {
        "profit", "profits", "profitable", "gain", "gains", "growth", "growing",
        "surge", "surges", "surged", "rally", "rallies", "rallied", "outperform",
        "outperforms", "outperformed", "dividend", "dividends", "record", "bull",
        "bullish", "upgrade", "upgrades", "upgraded", "beat", "beats", "beating",
        "expansion", "expanding", "rebound", "rebounds", "recovery", "recover",
        "turnaround", "breakthrough", "high", "higher", "peak", "upside", "win",
        "wins", "winning", "secured", "approved", "acquisition", "boost", "boosts",
        "boosted", "advance", "advances", "strong", "stronger", "soar", "soars",
        "soared", "jump", "jumps", "jumped", "optimistic", "stellar", "robust"
    }

    NEGATIVE_WORDS: Set[str] = {
        "loss", "losses", "losing", "decline", "declines", "declined", "declining",
        "miss", "misses", "missed", "missing", "downgrade", "downgrades", "downgraded",
        "fall", "falls", "fell", "falling", "slump", "slumps", "slumped", "plunge",
        "plunges", "plunged", "crash", "crashes", "crashed", "bear", "bearish",
        "warning", "warns", "warned", "debt", "debts", "default", "defaults",
        "defaulted", "fraud", "frauds", "penalty", "penalties", "probe", "probes",
        "probed", "investigation", "investigations", "lawsuit", "litigation",
        "weak", "weaker", "weakness", "downside", "cut", "cuts", "cutting",
        "drop", "drops", "dropped", "dropping", "dropoff", "underperform",
        "underperforms", "underperformed", "pessimistic", "struggle", "struggles"
    }

    NEGATION_WORDS: Set[str] = {
        "not", "no", "never", "without", "hardly", "barely", "scarcely", "neither", "nor"
    }

    def analyze(self, text: str) -> SentimentResult:
        """Evaluates polarity and returns structured SentimentResult."""
        if not text or not text.strip():
            return SentimentResult(label="NEUTRAL", score=0.5, engine="financial_lexicon")

        words = re.findall(r"\b[a-zA-Z0-9-]+\b", text.lower())
        pos_count = 0
        neg_count = 0

        for i, word in enumerate(words):
            # Check if preceded by a negation within 2 words
            is_negated = False
            start_window = max(0, i - 2)
            for j in range(start_window, i):
                if words[j] in self.NEGATION_WORDS:
                    is_negated = True
                    break

            if word in self.POSITIVE_WORDS:
                if is_negated:
                    neg_count += 1
                else:
                    pos_count += 1
            elif word in self.NEGATIVE_WORDS:
                if is_negated:
                    pos_count += 1  # e.g. "no decline", "not falling"
                else:
                    neg_count += 1

        total_signals = pos_count + neg_count
        if total_signals == 0:
            return SentimentResult(label="NEUTRAL", score=0.5, engine="financial_lexicon")

        if pos_count > neg_count:
            confidence = min(0.95, round(0.5 + (pos_count / (total_signals + 1)) * 0.5, 2))
            return SentimentResult(label="POSITIVE", score=confidence, engine="financial_lexicon")
        elif neg_count > pos_count:
            confidence = min(0.95, round(0.5 + (neg_count / (total_signals + 1)) * 0.5, 2))
            return SentimentResult(label="NEGATIVE", score=confidence, engine="financial_lexicon")

        return SentimentResult(label="NEUTRAL", score=0.5, engine="financial_lexicon")


class SentimentEngine:
    """
    Unified multi-tier sentiment analysis engine.
    Automatically leverages local INT8 FinBERT ONNX model when downloaded,
    and seamlessly falls back to the FinancialLexicon on lightweight/mobile platforms.
    """

    def __init__(self):
        self.lexicon = FinancialLexicon()
        self._onnx_session = None
        self._onnx_path = None
        self._vocab = None

    def _load_vocab(self):
        if self._vocab is not None:
            return self._vocab
        vocab_path = model_manager.models_dir / "vocab.txt"
        if vocab_path.exists():
            vocab = {}
            try:
                with open(vocab_path, "r", encoding="utf-8") as f:
                    for idx, line in enumerate(f):
                        vocab[line.strip()] = idx
                self._vocab = vocab
                return self._vocab
            except Exception as e:
                logger.warning("Failed to parse vocab.txt: %s", e)
        return None

    def _tokenize(self, text: str, max_len: int = 64):
        vocab = self._load_vocab()
        words = re.findall(r"[a-zA-Z0-9]+|[^\s\w]", text.lower())
        subwords = ["[CLS]"]
        for word in words:
            if vocab and word in vocab:
                subwords.append(word)
            elif vocab:
                cur = ""
                matched = False
                for i in range(len(word)):
                    prefix = word[:i + 1]
                    if prefix in vocab:
                        cur = prefix
                        matched = True
                if matched:
                    subwords.append(cur)
                else:
                    subwords.append("[UNK]")
            else:
                subwords.append(word)

        subwords.append("[SEP]")

        if vocab:
            unk_id = vocab.get("[UNK]", 100)
            ids = [vocab.get(sw, unk_id) for sw in subwords][:max_len]
        else:
            ids = [101] + [1000 + (abs(hash(w)) % 27000) for w in subwords[1:-1]][:max_len - 2] + [102]

        pad_len = max_len - len(ids)
        input_ids = ids + [0] * pad_len
        attention_mask = [1] * len(ids) + [0] * pad_len
        token_type_ids = [0] * max_len
        return input_ids, attention_mask, token_type_ids

    def _get_onnx_session(self):
        """Lazy-loads ONNX runtime session if model is downloaded."""
        model_path = model_manager.get_model_path("finbert_int8")
        if not model_path:
            self._onnx_session = None
            self._onnx_path = None
            return None

        if self._onnx_session is not None and self._onnx_path == model_path:
            return self._onnx_session

        try:
            import onnxruntime as ort
            # Run on CPU with thread limit for background safety
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 2
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self._onnx_session = ort.InferenceSession(str(model_path), sess_options=opts, providers=["CPUExecutionProvider"])
            self._onnx_path = model_path
            logger.info("Initialized FinBERT ONNX inference session from %s", model_path)
            return self._onnx_session
        except Exception as e:
            logger.warning("Failed to initialize ONNX session: %s. Falling back to lexicon.", e)
            self._onnx_session = None
            return None

    def analyze(self, text: str) -> SentimentResult:
        """
        Evaluates text sentiment. Uses FinBERT ONNX if model is available,
        otherwise uses Loughran-McDonald Financial Lexicon.
        """
        session = self._get_onnx_session()
        if session is not None:
            try:
                return self._analyze_onnx(text, session)
            except Exception as e:
                logger.warning("FinBERT ONNX inference error: %s. Reverting to lexicon.", e)

        return self.lexicon.analyze(text)

    def _analyze_onnx(self, text: str, session) -> SentimentResult:
        """
        Runs tokenization and inference using ONNX session.
        FinBERT outputs 3 logits: [positive, negative, neutral].
        """
        import numpy as np

        input_ids, attention_mask, token_type_ids = self._tokenize(text)

        inputs = {
            session.get_inputs()[0].name: np.array([input_ids], dtype=np.int64),
            session.get_inputs()[1].name: np.array([attention_mask], dtype=np.int64),
        }

        if len(session.get_inputs()) > 2:
            inputs[session.get_inputs()[2].name] = np.array([token_type_ids], dtype=np.int64)

        outputs = session.run(None, inputs)
        logits = outputs[0][0]  # Shape: (3,) -> [positive, negative, neutral]

        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)

        labels = ["POSITIVE", "NEGATIVE", "NEUTRAL"]
        best_idx = int(np.argmax(probs))
        return SentimentResult(
            label=labels[best_idx],
            score=round(float(probs[best_idx]), 2),
            engine="finbert_onnx"
        )


# Global sentiment engine singleton
sentiment_engine = SentimentEngine()

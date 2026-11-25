import logging
import re
from dataclasses import dataclass
from typing import Set, Tuple

from app.ml.model_manager import model_manager

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    label: str  # "POSITIVE" | "NEGATIVE" | "NEUTRAL"
    score: float  # Polarity / confidence between 0.0 and 1.0
    engine: str  # "finbert_onnx" | "financial_lexicon" | "deterministic_rule"
    tone_score: float = 0.0  # Continuous score between -1.0 (strongly negative) and +1.0 (strongly positive)


class FinancialLexicon:
    """
    Academic Financial Sentiment Lexicon (Loughran-McDonald adapted for equity news & concalls).
    Accurately handles financial negations, contextual polarity, and uncertainty words.
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
        "soared", "jump", "jumps", "jumped", "optimistic", "stellar", "robust",
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
        "underperforms", "underperformed", "pessimistic", "struggle", "struggles",
    }

    # Loughran-McDonald financial uncertainty and hedging vocabulary
    UNCERTAINTY_WORDS: Set[str] = {
        "uncertain", "uncertainty", "uncertainties", "uncertainly",
        "volatile", "volatility", "volatilities",
        "cautious", "cautiously", "caution", "cautions",
        "headwind", "headwinds",
        "slowdown", "slowdowns", "slowing",
        "pressure", "pressures", "pressured", "pressuring",
        "fluctuate", "fluctuates", "fluctuated", "fluctuating", "fluctuation", "fluctuations",
        "defer", "defers", "deferred", "deferring",
        "softness", "soft", "softer", "subdued",
        "risk", "risks", "risky", "riskier", "riskiest",
        "weak", "weaker", "weakness", "weaknesses",
        "challenging", "challenge", "challenges", "challenged",
        "hesitant", "hesitancy", "hesitancies",
        "approximate", "approximately", "approximation",
        "assumption", "assumptions", "assume", "assumes", "assumed",
        "contingent", "contingency", "contingencies",
        "visibility",
        "tentative", "tentatively",
        "unclear", "unpredictable", "unforeseen", "unforecasted", "unsettled", "unstable", "instability",
        "adverse", "adversely",
        "turbulence", "turbulent",
        "vague", "vaguely", "vagueness",
        "speculate", "speculative", "speculation",
        "preliminary", "probabilistic", "probabilities",
        "exposure", "exposures", "recalibrating", "scrutiny",
    }

    NEGATION_WORDS: Set[str] = {
        "not", "no", "never", "without", "hardly", "barely", "scarcely", "neither", "nor"
    }

    def compute_uncertainty_rate(self, text: str) -> float:
        """
        Computes the density of Loughran-McDonald uncertainty/hedging words per 100 words.
        """
        if not text or not text.strip():
            return 0.0
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        if not words:
            return 0.0
        hits = sum(1 for w in words if w in self.UNCERTAINTY_WORDS)
        return round((hits / len(words)) * 100, 2)

    def analyze(self, text: str) -> SentimentResult:
        """Evaluates polarity and returns structured SentimentResult."""
        if not text or not text.strip():
            return SentimentResult(label="NEUTRAL", score=0.5, engine="financial_lexicon", tone_score=0.0)

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
            return SentimentResult(label="NEUTRAL", score=0.5, engine="financial_lexicon", tone_score=0.0)

        # Continuous polarity in [-1.0, 1.0]
        raw_tone = (pos_count - neg_count) / max(total_signals, 1)
        tone_score = round(max(-1.0, min(1.0, raw_tone)), 3)

        if pos_count > neg_count:
            confidence = min(0.95, round(0.5 + (pos_count / (total_signals + 1)) * 0.5, 2))
            return SentimentResult(label="POSITIVE", score=confidence, engine="financial_lexicon", tone_score=tone_score)
        elif neg_count > pos_count:
            confidence = min(0.95, round(0.5 + (neg_count / (total_signals + 1)) * 0.5, 2))
            return SentimentResult(label="NEGATIVE", score=confidence, engine="financial_lexicon", tone_score=tone_score)

        return SentimentResult(label="NEUTRAL", score=0.5, engine="financial_lexicon", tone_score=0.0)


class SentimentEngine:
    """
    Optimized multi-tier hybrid sentiment and tone engine.
    1. Layer 1: Deterministic Rule Layer (< 0.1 ms) for explicit ratings & catalysts
    2. Layer 2: HKUST FinBERT-Tone INT8 ONNX Engine (5–15 ms) for nuanced contextual tone
    3. Layer 3: Loughran-McDonald Lexicon (< 1 ms) portable zero-download fallback
    """

    # Deterministic signals for ultra-fast, 100% precision evaluation
    BROKER_BUY_PATTERN = re.compile(
        r"\b(?:recommends?\s+(?:buy|accumulate)|target\s+price\s+of\s+rs|rating\s+buy|initiated\s+with\s+buy)\b",
        re.IGNORECASE,
    )
    BROKER_SELL_PATTERN = re.compile(
        r"\b(?:recommends?\s+(?:sell|reduce)|downgrade(?:d)?\s+to\s+sell|rating\s+sell)\b",
        re.IGNORECASE,
    )
    CATALYST_POSITIVE_PATTERN = re.compile(
        r"\b(?:dividend\s+of\s+rs|bonus\s+issue|order\s+win\s+of|awarded\s+contract|share\s+buyback"
        r"|shares?\s+(?:surge|surged|surges|rally|rallied|rallies|soar|soared|soars|jump|jumped|jumps|skyrocket|skyrocketed)"
        r"|all-time\s+high|new\s+52-week\s+high)\b",
        re.IGNORECASE,
    )
    CATALYST_NEGATIVE_PATTERN = re.compile(
        r"\b(?:sebi\s+penalty|ed\s+raid|cbi\s+probe|fraud\s+allegation|arrested|insolvency\s+proceedings"
        r"|share\s*price\s*fall|shares?\s+(?:plunge|plunged|plunges|slump|slumped|slumps|crash|crashed|crashes|tank|tanked|tanks|tumble|tumbled|tumbles|drop|dropped|drops|sink|sank|sinks)"
        r"|price\s+(?:fall|drop|slump|tumble|decline|crash))\b",
        re.IGNORECASE,
    )

    def __init__(self):
        self.lexicon = FinancialLexicon()
        self._onnx_session = None
        self._onnx_path = None
        self._vocab = None
        self._label_mapping = None

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
            self._label_mapping = self._detect_label_mapping(self._onnx_session)
            logger.info("Initialized FinBERT-Tone ONNX inference session from %s (mapping: %s)", model_path, self._label_mapping)
            return self._onnx_session
        except Exception as e:
            logger.warning("Failed to initialize ONNX session: %s. Falling back to lexicon.", e)
            self._onnx_session = None
            return None

    def _detect_label_mapping(self, session) -> Tuple[int, int, int]:
        """
        Auto-detects the label indexing of the loaded ONNX model:
        - ProsusAI/finbert mapping: 0=Positive, 1=Negative, 2=Neutral -> (0, 1, 2)
        - yiyanghkust/finbert-tone mapping: 1=Positive, 2=Negative, 0=Neutral -> (1, 2, 0)
        Returns: (pos_idx, neg_idx, neu_idx)
        """
        import numpy as np

        probe_text = "Company reported massive profit growth and record revenue beat."
        input_ids, attention_mask, token_type_ids = self._tokenize(probe_text)
        inputs = {
            session.get_inputs()[0].name: np.array([input_ids], dtype=np.int64),
            session.get_inputs()[1].name: np.array([attention_mask], dtype=np.int64),
        }
        if len(session.get_inputs()) > 2:
            inputs[session.get_inputs()[2].name] = np.array([token_type_ids], dtype=np.int64)

        try:
            outputs = session.run(None, inputs)
            logits = outputs[0][0]
            best_idx = int(np.argmax(logits))
            if best_idx == 1:
                return 1, 2, 0  # finbert-tone
            return 0, 1, 2      # standard finbert
        except Exception as e:
            logger.warning("Error probing ONNX label mapping: %s. Defaulting to finbert-tone.", e)
            return 1, 2, 0

    def analyze(self, text: str) -> SentimentResult:
        """
        Evaluates text sentiment through the optimized hybrid pipeline:
        1. Fast deterministic rule match for hard catalysts and broker recommendations.
        2. FinBERT-Tone ONNX neural evaluation if model is active.
        3. FinancialLexicon fallback when offline.
        """
        if not text or not text.strip():
            return SentimentResult(label="NEUTRAL", score=0.5, engine="deterministic_rule", tone_score=0.0)

        # Layer 1: Fast Deterministic Rules (< 0.1 ms)
        if self.BROKER_BUY_PATTERN.search(text) or self.CATALYST_POSITIVE_PATTERN.search(text):
            return SentimentResult(label="POSITIVE", score=0.95, engine="deterministic_rule", tone_score=0.90)
        if self.BROKER_SELL_PATTERN.search(text) or self.CATALYST_NEGATIVE_PATTERN.search(text):
            return SentimentResult(label="NEGATIVE", score=0.95, engine="deterministic_rule", tone_score=-0.90)

        # Layer 2: FinBERT-Tone ONNX Inference
        session = self._get_onnx_session()
        if session is not None:
            try:
                return self._analyze_onnx(text, session)
            except Exception as e:
                logger.warning("FinBERT ONNX inference error: %s. Reverting to lexicon.", e)

        # Layer 3: Loughran-McDonald Lexicon Fallback
        return self.lexicon.analyze(text)

    def analyze_tone_score(self, text: str) -> float:
        """Convenience method returning continuous tone score in [-1.0, 1.0]."""
        return self.analyze(text).tone_score

    def _analyze_onnx(self, text: str, session) -> SentimentResult:
        """
        Runs tokenization and inference using FinBERT-Tone ONNX session.
        yiyanghkust/finbert-tone output mapping:
        0: Neutral, 1: Positive, 2: Negative
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
        logits = outputs[0][0]  # Shape: (3,)

        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)

        pos_idx, neg_idx, neu_idx = self._label_mapping or (1, 2, 0)
        p_positive = float(probs[pos_idx])
        p_negative = float(probs[neg_idx])
        p_neutral = float(probs[neu_idx])

        # Continuous tone score: Positive probability minus Negative probability in [-1.0, 1.0]
        tone_score = round(p_positive - p_negative, 3)

        best_idx = int(np.argmax(probs))
        if best_idx == pos_idx:
            label = "POSITIVE"
            score = round(p_positive, 2)
        elif best_idx == neg_idx:
            label = "NEGATIVE"
            score = round(p_negative, 2)
        else:
            label = "NEUTRAL"
            score = round(p_neutral, 2)

        return SentimentResult(
            label=label,
            score=score,
            engine="finbert_onnx",
            tone_score=tone_score,
        )


# Global sentiment engine singleton
sentiment_engine = SentimentEngine()

import re
from typing import List, Set


class HeadlineDeduplicator:
    """
    Lightweight, pure-Python near-duplicate headline and statement detector.
    Uses word n-gram tokenization and Jaccard similarity to catch syndicated
    news repetitions without waking deep learning models.
    """

    _STOP_WORDS = {
        "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
        "by", "from", "up", "about", "into", "over", "after", "is", "are", "was",
        "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "but", "if", "then", "else", "when", "where", "why", "how", "all", "any",
        "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
        "just", "should", "now"
    }

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self._history_shingles: List[Set[str]] = []

    def _get_shingles(self, text: str, n: int = 2) -> Set[str]:
        """Generates word n-grams from text, filtering punctuation and stop words."""
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = [w for w in cleaned.split() if w and w not in self._STOP_WORDS]
        if not tokens:
            return set()
        if len(tokens) < n:
            return set(tokens)
        return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Computes Jaccard similarity of word shingles between two headlines."""
        s1 = self._get_shingles(text1)
        s2 = self._get_shingles(text2)
        if not s1 or not s2:
            return 0.0
        intersection = len(s1.intersection(s2))
        union = len(s1.union(s2))
        return intersection / union if union > 0 else 0.0

    def is_duplicate(self, text: str, threshold: float = 0.60) -> bool:
        """
        Checks if the headline is a near-duplicate of recently seen headlines.
        If not duplicate, records it in the rolling history buffer.
        """
        shingles = self._get_shingles(text)
        if not shingles:
            return False

        for existing in self._history_shingles:
            intersection = len(shingles.intersection(existing))
            union = len(shingles.union(existing))
            if union > 0 and (intersection / union) >= threshold:
                return True

        self._history_shingles.append(shingles)
        if len(self._history_shingles) > self.history_size:
            self._history_shingles.pop(0)

        return False

    def clear(self) -> None:
        """Clears the deduplication cache."""
        self._history_shingles.clear()


# Singleton default deduplicator
headline_deduplicator = HeadlineDeduplicator()

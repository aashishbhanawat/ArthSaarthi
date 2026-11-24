import collections
import math
import re
from typing import Any, Dict, List, Set, Tuple

from app.ml.sentiment_engine import sentiment_engine


class ConcallAnalyzer:
    """
    Extractive Intelligence Engine for Earnings Conference Calls & Corporate Disclosures.
    Operates 100% locally on edge without requiring generative Large Language Models:
    1. Structural sectioning (Management Discussion vs. Analyst Q&A)
    2. FinBERT Tone & Sentiment Profiling
    3. Deterministic Guidance, Capex, and Margin Extraction
    4. Graph-Centrality Extractive Summarization (TextRank / TF-IDF)
    5. Salient Discussion Theme & Keyword Mining
    """

    # Phrases marking the transition from management remarks to Q&A session
    QA_DELIMITERS = [
        r"question[-\s]*and[-\s]*answer\s*session",
        r"q\s*&\s*a\s*session",
        r"floor\s*is\s*(?:now\s*)?open\s*for\s*questions",
        r"begin\s*(?:the\s*)?question[-\s]*and[-\s]*answer",
        r"take\s*the\s*first\s*question",
        r"first\s*question\s*comes\s*from",
        r"questions\s*from\s*analysts",
    ]

    # Common corporate pleasantries / boilerplate to filter out of extractive highlights
    BOILERPLATE_PATTERNS = [
        r"welcome\s*(?:you\s*)?all\s*to",
        r"thank\s*you\s*(?:very\s*much)?\s*for\s*(?:joining|attending)",
        r"good\s*(?:morning|afternoon|evening)",
        r"safe\s*harbor\s*statement",
        r"forward[-\s]*looking\s*statements?",
        r"hand\s*(?:over\s*)?the\s*call\s*to",
        r"turn\s*(?:over\s*)?the\s*call\s*to",
        r"ladies\s*and\s*gentlemen",
        r"operator\s*:",
        r"conference\s*call\s*recording",
        r"dial[-\s]*in\s*numbers?",
    ]

    # Corporate stop words for theme extraction
    STOP_WORDS: Set[str] = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can", "cannot", "could", "did", "do",
        "does", "doing", "down", "during", "each", "few", "for", "from", "further",
        "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
        "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
        "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of",
        "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
        "out", "over", "own", "same", "she", "should", "so", "some", "such", "than",
        "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these",
        "they", "this", "those", "through", "to", "too", "under", "until", "up", "very",
        "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
        "why", "with", "would", "you", "your", "yours", "yourself", "yourselves",
        # Corporate call conversational filler
        "thank", "thanks", "sir", "madam", "welcome", "please", "yes", "no", "okay",
        "like", "know", "think", "said", "say", "saying", "see", "call", "quarter",
        "company", "management", "analyst", "question", "answer", "operator", "line",
        "participants", "ladies", "gentlemen", "participant", "hand", "turn", "next",
    }

    def segment_transcript(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Splits transcript into (management_sentences, qa_sentences).
        """
        raw_sentences = self._split_sentences(text)
        if not raw_sentences:
            return [], []

        qa_split_idx = -1
        combined_text = text.lower()

        # Find position of QA delimiter
        for pat in self.QA_DELIMITERS:
            m = re.search(pat, combined_text, re.IGNORECASE)
            if m:
                # Find which sentence index contains or follows this match
                char_pos = m.start()
                curr_char_idx = 0
                for idx, sent in enumerate(raw_sentences):
                    curr_char_idx += len(sent)
                    if curr_char_idx >= char_pos:
                        qa_split_idx = idx
                        break
                break

        if qa_split_idx != -1 and qa_split_idx < len(raw_sentences):
            mgmt = raw_sentences[:qa_split_idx]
            qa = raw_sentences[qa_split_idx:]
            return mgmt, qa

        # Default fallback: First 40% management remarks, remaining 60% Q&A
        split_pt = max(1, int(len(raw_sentences) * 0.40))
        return raw_sentences[:split_pt], raw_sentences[split_pt:]

    def _split_sentences(self, text: str) -> List[str]:
        """Cleans and tokenizes text into distinct sentences."""
        cleaned = re.sub(r"\r\n|\r", "\n", text)
        cleaned = re.sub(r"\n+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Split on sentence terminals
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'₹])", cleaned)
        sentences: List[str] = []
        for p in parts:
            p_strip = p.strip()
            if len(p_strip) >= 25:  # Skip tiny fragments
                sentences.append(p_strip)
        return sentences

    def _is_boilerplate(self, sentence: str) -> bool:
        """Returns True if the sentence is administrative or conversational boilerplate."""
        sent_lower = sentence.lower()
        for pat in self.BOILERPLATE_PATTERNS:
            if re.search(pat, sent_lower):
                return True
        return False

    def analyze_tone(self, sentences: List[str]) -> Dict[str, Any]:
        """
        Computes sentiment percentage breakdown across a collection of sentences
        using FinBERT INT8 ONNX or fallback FinancialLexicon.
        """
        if not sentences:
            return {
                "positive_pct": 0.0,
                "neutral_pct": 100.0,
                "negative_pct": 0.0,
                "overall": "NEUTRAL",
                "sample_size": 0,
            }

        counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
        scored_sentences = [s for s in sentences if not self._is_boilerplate(s)]
        if not scored_sentences:
            scored_sentences = sentences

        for s in scored_sentences:
            res = sentiment_engine.analyze(s)
            lbl = getattr(res, "label", "NEUTRAL")
            counts[lbl] = counts.get(lbl, 0) + 1

        total = sum(counts.values()) or 1
        pos_pct = round((counts["POSITIVE"] / total) * 100, 1)
        neu_pct = round((counts["NEUTRAL"] / total) * 100, 1)
        neg_pct = round((counts["NEGATIVE"] / total) * 100, 1)

        if pos_pct >= neg_pct + 15.0 and pos_pct >= 35.0:
            overall = "BULLISH"
        elif neg_pct >= pos_pct + 10.0 and neg_pct >= 30.0:
            overall = "BEARISH"
        elif neu_pct >= 60.0:
            overall = "NEUTRAL"
        else:
            overall = "BALANCED"

        return {
            "positive_pct": pos_pct,
            "neutral_pct": neu_pct,
            "negative_pct": neg_pct,
            "overall": overall,
            "sample_size": len(scored_sentences),
        }

    def mine_guidance_metrics(self, text: str) -> List[Dict[str, str]]:
        """
        Extracts forward-looking financial targets, Capex plans, margins, and debt metrics.
        """
        results: List[Dict[str, str]] = []
        sentences = self._split_sentences(text)
        seen_snippets: Set[str] = set()

        for sent in sentences:
            if self._is_boilerplate(sent):
                continue

            sent_clean = sent.strip()

            # 1. Capex & Plant Expansion
            has_capex_kw = any(w in sent_clean.lower() for w in ["capex", "capital expenditure", "gigafactory", "plant expansion"])
            has_money = re.search(r"(?:₹|Rs\.?|INR|\$)?\s*\d+(?:,\d+)*(?:\.\d+)?\s*(?:cr|crore|lakh|mn|bn|billion|million)", sent_clean, re.I)
            if has_capex_kw and has_money and "Capex" not in seen_snippets:
                results.append({"category": "Capex", "text": sent_clean})
                seen_snippets.add("Capex")
                continue

            # 2. Margin & EBITDA Outlook
            has_margin_kw = any(w in sent_clean.lower() for w in ["margin", "ebitda"])
            has_pct_or_bps = re.search(r"\b(?:\d+(?:\.\d+)?\s*%|\d+\s*bps)\b", sent_clean, re.I)
            if has_margin_kw and has_pct_or_bps and "Margin" not in seen_snippets:
                results.append({"category": "Margin Outlook", "text": sent_clean})
                seen_snippets.add("Margin")
                continue

            # 3. Growth & Revenue Guidance
            has_growth_kw = any(w in sent_clean.lower() for w in ["guidance", "target", "forecast", "revenue growth", "volume growth"])
            has_pct = re.search(r"\b\d+(?:\.\d+)?\s*%", sent_clean)
            if has_growth_kw and has_pct and "Growth" not in seen_snippets:
                results.append({"category": "Guidance & Growth", "text": sent_clean})
                seen_snippets.add("Growth")
                continue

            # 4. Debt & Deleveraging
            has_debt_kw = any(w in sent_clean.lower() for w in ["debt", "net debt", "borrowings", "repayment", "deleverag"])
            has_num = re.search(r"(?:₹|Rs\.?|INR|\$)?\s*\d+(?:,\d+)*(?:\.\d+)?\s*(?:cr|crore|lakh|mn|bn|billion|million)?", sent_clean, re.I)
            if has_debt_kw and has_num and "Debt" not in seen_snippets:
                results.append({"category": "Debt & Balance Sheet", "text": sent_clean})
                seen_snippets.add("Debt")
                continue

        return results[:4]

    def extract_top_sentences(self, text: str, n: int = 5) -> List[str]:
        """
        Extractive Summarization using TF-IDF Graph Centrality (TextRank style).
        Selects top N most informative verbatim sentences with zero generative hallucination.
        """
        sentences = [s for s in self._split_sentences(text) if not self._is_boilerplate(s)]
        if len(sentences) <= n:
            return sentences

        # Tokenize sentences into word bags
        word_bags: List[List[str]] = []
        doc_freq: collections.Counter = collections.Counter()
        for sent in sentences:
            words = [
                w.lower()
                for w in re.findall(r"\b[a-zA-Z]{3,}\b", sent)
                if w.lower() not in self.STOP_WORDS
            ]
            word_bags.append(words)
            doc_freq.update(set(words))

        num_docs = len(sentences)

        # Compute TF-IDF vectors
        vectors: List[Dict[str, float]] = []
        for bag in word_bags:
            term_freq = collections.Counter(bag)
            vec: Dict[str, float] = {}
            for word, count in term_freq.items():
                idf = math.log((num_docs + 1) / (doc_freq[word] + 1)) + 1.0
                vec[word] = count * idf
            # Normalize vector
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            vectors.append({w: v / norm for w, v in vec.items()})

        # Pairwise Cosine Similarity Centrality Scores
        centrality_scores = [0.0] * num_docs
        for i in range(num_docs):
            for j in range(i + 1, num_docs):
                # Dot product of normalized vectors
                sim = sum(vectors[i].get(w, 0.0) * vectors[j].get(w, 0.0) for w in vectors[i])
                centrality_scores[i] += sim
                centrality_scores[j] += sim

        # Bonus for presence of financial figures (numbers, percentages, capex)
        for i, sent in enumerate(sentences):
            if re.search(r"\b(?:\d+%(?:\.\d+)?|₹|Rs\.?|\bcr\b|\bcrore\b|\bebitda\b|\bguidance\b)", sent, re.I):
                centrality_scores[i] *= 1.3

        # Rank and pick top N sentences preserving original narrative flow
        ranked_indices = sorted(range(num_docs), key=lambda idx: centrality_scores[idx], reverse=True)[:n]
        ranked_indices.sort()  # Restore original transcript order

        return [sentences[idx] for idx in ranked_indices]

    def extract_topics(self, text: str, n: int = 6) -> List[str]:
        """
        Extracts top N salient discussion topics (n-grams) from the concall text.
        """
        words = [
            w.lower()
            for w in re.findall(r"\b[a-zA-Z]{3,}\b", text)
            if w.lower() not in self.STOP_WORDS
        ]
        if not words:
            return []

        # Count bi-grams and tri-grams
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
        counter = collections.Counter(bigrams)

        # Title-case formatted top topics
        top = [
            bg.title()
            for bg, count in counter.most_common(n * 2)
            if not any(sw in bg for sw in ["first question", "good afternoon", "thank you", "next question"])
        ]
        return top[:n]

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Runs full end-to-end non-LLM concall intelligence analysis.
        """
        mgmt_sents, qa_sents = self.segment_transcript(text)

        mgmt_tone = self.analyze_tone(mgmt_sents)
        qa_tone = self.analyze_tone(qa_sents)
        guidance = self.mine_guidance_metrics(text)
        takeaways = self.extract_top_sentences(text, n=5)
        topics = self.extract_topics(text, n=6)

        return {
            "management_tone": mgmt_tone,
            "qa_tone": qa_tone,
            "guidance_metrics": guidance,
            "top_takeaways": takeaways,
            "key_themes": topics,
            "sentence_count": len(mgmt_sents) + len(qa_sents),
        }


# Global singleton instance
concall_analyzer = ConcallAnalyzer()

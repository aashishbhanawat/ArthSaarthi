import collections
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.ml.sentiment_engine import sentiment_engine


class ConcallAnalyzer:
    """
    Extractive Intelligence Engine for Earnings Conference Calls & Corporate Disclosures.
    Operates 100% locally on edge without requiring generative Large Language Models:
    1. Structural sectioning (Management Discussion vs. Analyst Q&A)
    2. FinBERT-Tone Sentiment & Tone Profiling (Continuous Polarity [-1.0, +1.0])
    3. Prepared Remarks vs. Q&A Tone Divergence Detection (Tone Gap Alert)
    4. Loughran-McDonald Hedging & Financial Uncertainty Index
    5. 4-Aspect Financial Sentiment Scorecard (Demand, Margins, Guidance, CapEx)
    6. Extractive Red Flags & Cautionary Risk Statements
    7. Deterministic Guidance, Capex, and Margin Extraction
    8. Graph-Centrality Extractive Summarization (TextRank / TF-IDF) with Concrete Statement Scoring
    9. Salient Discussion Theme & Domain Topic Mining
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

    # Administrative and pleasantry boilerplate to discard
    BOILERPLATE_PATTERNS = [
        r"welcome\s*(?:you\s*)?all\s*to",
        r"thank\s*you\s*(?:very\s*much)?\s*for\s*(?:joining|attending|the\s*question)?",
        r"good\s*(?:morning|afternoon|evening|day)",
        r"safe\s*harbor\s*statement",
        r"forward[-\s]*looking\s*statements?",
        r"hand\s*(?:over\s*)?the\s*call\s*to",
        r"turn\s*(?:over\s*)?the\s*call\s*to",
        r"ladies\s*and\s*gentlemen",
        r"operator\s*:",
        r"moderator\s*:",
        r"conference\s*call\s*recording",
        r"dial[-\s]*in\s*numbers?",
    ]

    # Conversational padding and non-substantive transition fragments
    FILLER_PATTERNS = [
        r"^(?:so\s+)?let\s+me\s+take\s+(?:the\s+)?(?:first|next|this)\s+(?:one|question)",
        r"^(?:coming\s+to\s+your\s+(?:first|second|next|last)?\s*question|to\s+answer\s+your\s+question)",
        r"^(?:as\s+(?:i|we)\s+(?:said|mentioned|explained|highlighted)|like\s+(?:i|we)\s+said)\b",
        r"^(?:i\s+think\s+so|i\s+would\s+say\s*so|we\s+believe\s+so)\.?$",
        r"^(?:yes|yeah|sure|okay|right|correct|absolutely|no),?\s*(?:sir|madam)?\.?$",
        r"^i\s+will\s+request\s+.*?\s+to\s+(?:take|answer)\s+this",
        r"^(?:we|i)\s+will\s+be\s+the\s+first\s+one\.?$",
    ]

    # Speaker prefix pattern (e.g. "Avik Roy:", "Management:", "Q - Prabhu Roy:")
    SPEAKER_PREFIX_PATTERN = re.compile(
        r"^(?:(?:[A-Z][a-zA-Z\s\.\-']{1,35}|Operator|Moderator|Analyst|Management)\s*:\s*|(?:[QA]\s*-\s*[A-Z][a-zA-Z\s\.\-']{1,35}\s*:\s*))"
    )

    # Topic anchors for aspect-level sentiment routing
    TOPIC_ANCHORS = {
        "demand_revenue": "revenue growth order book volume demand customer sales pipeline bookings market share shipments delivery",
        "margins_costs": "ebitda gross margin operating profit cost raw material inflation pricing realization overheads input costs",
        "guidance_outlook": "full year guidance outlook visibility target forecast next quarter fiscal forward trajectory expectations",
        "capex_debt": "capital expenditure capex gigafactory debt repayment working capital liquidity cash flow borrowings deleveraging",
    }

    # Corporate stop words and artifacts for topic/theme extraction
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
        # Auxiliary & modal verbs
        "will", "shall", "would", "could", "can", "may", "might", "must",
        # Numerals and ordinals
        "first", "second", "third", "one", "two", "three", "take", "look", "lot", "bit",
        "thing", "things", "way", "point", "put", "together", "come", "coming",
        # Corporate legal entity suffixes & executive titles
        "industries", "limited", "ltd", "corp", "corporation", "inc", "holdings",
        "enterprises", "technologies", "private", "pvt", "director", "finance",
        "officer", "chief", "executive", "president", "managing", "cfo", "ceo", "coo",
        "percent", "percentage", "row", "rows",
        # Document and presentation artifacts
        "page", "pages", "slide", "presentation", "transcript", "session", "dialogue",
        "january", "february", "march", "april", "may", "june", "july", "august",
        "september", "october", "november", "december",
        "good", "day", "conference", "full", "year", "years", "let", "also",
        # Common general verbs / non-thematic words
        "contribute", "contributes", "contributed", "almost", "grown", "growing",
        "slowly", "running", "across", "around", "business", "give", "giving",
        "well", "much", "many", "couple", "ramp", "minimum", "maximum", "target",
    }

    INFO_ANCHORS = re.compile(
        r"(?:\d+%|\bINR\b|\$\d+|\b₹\d+|\b\d+\s*(?:cr|crore|lakh|bn|mn|bps|gwh|mwh|mw|gw)\b|"
        r"\bEBITDA\b|\bROCE\b|\bmargin|\bdemand\b|\bcapacity\b|\bwarranty\b|\bOEM|\bcapex\b|"
        r"\brevenue|\butilization\b|\bantimony\b|\blithium\b|\bgrowth\b|\bprofit|\bcost|"
        r"\bpricing\b|\bheadwind|\bvolatil)",
        re.I,
    )

    THEME_STOP_PHRASES = {
        "double digit", "single digit", "last year", "next year",
        "current year", "first quarter", "fourth quarter", "second quarter",
        "third quarter", "full year", "going forward", "few years", "couple years",
        "next couple", "past year", "previous year", "director finance",
        "chief financial", "managing director", "conference call", "earnings call",
        "per row", "per crore", "higher percent", "growth percent", "get orders",
        "percent", "percentage", "half ended", "metric tons", "million metric", "kilo right",
        "going pay", "pay rent",
    }

    HONORIFICS = re.compile(r"\b(?:mr|ms|mrs|dr|shri|smt|ca)\.?\s*", re.IGNORECASE)

    def _clean_transcript(self, text: str) -> str:
        """Strips document pagination, PDF headers/footers, and repairs wrapped line boundaries."""
        t = re.sub(r"\r\n|\r", "\n", text)
        t = re.sub(r"(?i)\bpage\s*\d+\s*(?:of\s*\d+)?\b", "", t)
        t = re.sub(r"(?i)\b\d+\s*of\s*\d+\b", "", t)
        t = re.sub(
            r"(?i)\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b",
            "",
            t,
        )
        t = re.sub(
            r"(?i)\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b",
            "",
            t,
        )
        # Strip running page headers like "Exide Industries Limited ... Page X of Y"
        t = re.sub(
            r"(?i)[A-Z][a-zA-Z\s\.\-']+\s+[A-Za-z]+\s+\d{1,2},?\s+\d{4}\s+Page\s+\d+\s+of\s+\d+",
            " ",
            t,
        )
        # Repair missing periods across PDF line wraps before capitalized words
        t = re.sub(r"([a-z0-9])\s*\n+\s*([A-Z][a-z]+)", r"\1. \2", t)
        return t

    @classmethod
    def normalize_speaker_name(cls, name: str) -> str:
        name = cls.HONORIFICS.sub("", name).strip()
        name = re.sub(r"[^a-zA-Z\s.]", "", name)
        return re.sub(r"\s+", " ", name).lower().strip()

    def discover_speakers(self, raw_text: str) -> Dict[str, Any]:
        """
        Automatically identifies Management executives vs. Analysts from Indian BSE/NSE concall transcripts:
        - Pass A: Parses explicit MANAGEMENT: header block (Pages 1-2).
        - Pass B: Extracts analysts announced by Moderator cues ('from the line of <Name> from <Brokerage>').
        - Pass C: Extracts dialogue turns ('<Speaker>: <Utterance>') and uses frequency heuristics (>=3 turns = mgmt).
        - Splits turns and extracts clean management and analyst sentence streams.
        """
        cleaned = re.sub(r"(?i)\bpage\s+\d+\s+of\s+\d+\b", " ", raw_text)
        cleaned = re.sub(r"([a-z0-9])\s*\n+\s*([A-Z][a-z]+)", r"\1. \2", cleaned)
        cleaned = re.sub(r"\s*\n+\s*", " ", cleaned)

        mgmt_names: Set[str] = set()
        analyst_names: Set[str] = set()

        # Pass A: Parse explicit "MANAGEMENT:" header block if present (e.g. Exide, Chorus Call)
        header_match = re.search(
            r"(?i)MANAGEMENT\s*:\s*(.*?)(?=MODERATOR\s*:|Moderator\s*:|Question-and-Answer|Management\s+Discussion)",
            cleaned,
            flags=re.DOTALL,
        )
        if header_match:
            block = header_match.group(1)
            for m in re.finditer(
                r"(?:MR|MS|MRS|DR)\.?\s+([A-Z][A-Za-z\s.]{2,35}?)(?=\s*[–\-—,]|\s+CHIEF|\s+MANAGING|\s+DIRECTOR|\s+PRESIDENT|\s+HEAD|\s+EXECUTIVE|\s+SENIOR)",
                block,
                flags=re.IGNORECASE,
            ):
                norm = self.normalize_speaker_name(m.group(1))
                if norm and len(norm) > 2:
                    mgmt_names.add(norm)

        # Pass B: Extract analysts announced by Moderator ("from the line of <Name> from/with <Firm>")
        for m in re.finditer(
            r"(?i)(?:from the line of|question is from|line of)\s+([A-Z][a-zA-Z.\s]{2,35}?)(?=\s+(?:from|with|,|an Individual|\.))",
            cleaned,
        ):
            norm = self.normalize_speaker_name(m.group(1))
            if norm and len(norm) > 2:
                analyst_names.add(norm)

        # Pass C: Split all dialogue turns ("Speaker Name: text")
        turn_pattern = re.compile(
            r"(?:^|\s)([A-Z][a-zA-Z.]+(?:\s+[A-Z][a-zA-Z.]+){0,3})\s*:\s*"
        )
        matches = list(turn_pattern.finditer(cleaned))
        turns: List[Tuple[str, str, int]] = []
        speaker_turn_counts: collections.Counter = collections.Counter()

        for i, m in enumerate(matches):
            raw_speaker = m.group(1).strip()
            norm = self.normalize_speaker_name(raw_speaker)
            if norm in {"sub", "ref", "note", "cin", "email", "phone", "encl", "q", "a", "question", "answer"}:
                continue
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
            utterance = cleaned[start:end].strip()
            turns.append((norm, utterance, m.start()))
            if norm not in {"moderator", "operator"} and norm not in analyst_names:
                speaker_turn_counts[norm] += 1

        # Check for explicit management tags in dialogue turns (e.g. "Management:", "Executive:", "Opening Remarks:")
        for spk, _, _ in turns:
            if any(term in spk for term in {"management", "executive", "mgmt", "cfo", "ceo", "director", "opening remarks", "prepared remarks", "presentation"}):
                mgmt_names.add(spk)

        # Fallback: If Pass A found nothing, anyone answering >= 2 separate turns is Management
        if not mgmt_names:
            mgmt_names = {spk for spk, cnt in speaker_turn_counts.items() if cnt >= 2}

        # Middle-name variations (e.g. "Manoj Kumar Agarwal" vs "Manoj Agarwal")
        mgmt_first_last: Set[str] = set()
        for name in mgmt_names:
            parts = name.split()
            if len(parts) >= 2:
                mgmt_first_last.add(f"{parts[0]} {parts[-1]}")

        analyst_first_last: Set[str] = set()
        for name in analyst_names:
            parts = name.split()
            if len(parts) >= 2:
                analyst_first_last.add(f"{parts[0]} {parts[-1]}")

        # Identify where Q&A session starts in cleaned text
        qa_char_pos = -1
        for pat in self.QA_DELIMITERS:
            m_qa = re.search(pat, cleaned, re.IGNORECASE)
            if m_qa:
                qa_char_pos = m_qa.start()
                break

        # Route every turn into Management (Prepared vs Q&A) vs Analyst buckets
        mgmt_prepared_sents: List[str] = []
        mgmt_qa_sents: List[str] = []
        analyst_sents: List[str] = []
        seen_first_analyst = False

        for spk, utterance, start_pos in turns:
            if spk in {"moderator", "operator"}:
                continue
            parts = spk.split()
            fl = f"{parts[0]} {parts[-1]}" if len(parts) >= 2 else spk

            # Split turn into individual clean sentences
            raw_turn_sents = [
                s.strip()
                for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'₹])", utterance)
                if len(s.strip()) >= 20
            ]

            is_qa = (start_pos >= qa_char_pos) if qa_char_pos != -1 else seen_first_analyst

            if spk in mgmt_names or fl in mgmt_first_last or (not is_qa and spk not in analyst_names and fl not in analyst_first_last):
                for s in raw_turn_sents:
                    if not self._is_analyst_question(s):
                        if is_qa:
                            mgmt_qa_sents.append(s)
                        else:
                            mgmt_prepared_sents.append(s)
            else:
                if spk in analyst_names or fl in analyst_first_last or is_qa:
                    seen_first_analyst = True
                    for s in raw_turn_sents:
                        analyst_sents.append(s)

        mgmt_sents = mgmt_prepared_sents + mgmt_qa_sents

        return {
            "discovered_management": sorted(mgmt_names),
            "discovered_analysts": sorted(analyst_names),
            "mgmt_sentences": mgmt_sents,
            "mgmt_prepared_sentences": mgmt_prepared_sents,
            "mgmt_qa_sentences": mgmt_qa_sents,
            "analyst_sentences": analyst_sents,
        }

    def _extract_speaker_names(self, text: str) -> Set[str]:
        """Extracts individual executive and analyst name tokens to avoid them polluting topics."""
        names: Set[str] = set()
        matches = re.findall(r"(?:^|\n)\s*(?:[QA]\s*-\s*)?([A-Z][a-zA-Z\s\.\-']{2,30})\s*:", text)
        for m in matches:
            m_clean = m.strip()
            if m_clean.lower() not in {"operator", "moderator", "analyst", "management", "question", "answer"}:
                for part in re.findall(r"[a-zA-Z]{3,}", m_clean):
                    names.add(part.lower())
        return names

    def _clean_sentence(self, sentence: str) -> str:
        """Strips speaker prefixes and conversational padding from a candidate sentence."""
        s = self.SPEAKER_PREFIX_PATTERN.sub("", sentence).strip()
        s = re.sub(
            r"^(?:so\s+(?:i\s+would\s+say|let\s+me\s+(?:say|tell|take)|to\s+answer\s+that),?\s*|i\s+would\s+say,?\s*|now\s+the\s+business\s+is\s+like\s+this,?\s*|you\s+know,?\s*|as\s+you\s+know,?\s*|look,?\s*|see,?\s*)",
            "",
            s,
            flags=re.IGNORECASE,
        ).strip()
        if s and s[0].islower():
            s = s[0].upper() + s[1:]
        return s

    def _is_analyst_question(self, sentence: str) -> bool:
        """Identifies analyst inquiries to exclude them from management takeaways."""
        s = sentence.strip()
        if "?" in s:
            return True
        # Explicit analyst or question labels
        if re.search(
            r"(?i)^(?:[QA]\s*[:\-]|Question\s*:|Analyst\s*:|Participant\s*:|[A-Z][a-zA-Z\s\.\-']+\s*\([^\)]*(?:Analyst|Research|Securities|Capital)[^\)]*\)\s*:)",
            s,
        ):
            return True
        # Interrogative starts
        if re.search(
            r"^(?:what|why|how|could you|can you|would you|is there|are there|will you|do you|did you|have you|may i|any color on|any update on|could we|can we|am i|should we)\b",
            s,
            re.IGNORECASE,
        ):
            return True
        # Interrogative or question phrases anywhere in the sentence
        if re.search(
            r"\b(?:could you|can you|would you|will you|may i|can we|could we|tell us|help (?:us|me) understand|wanted to (?:understand|ask|know|check|clarify)|my (?:first|second|next|last)?\s*question|any color on|any update on|what sort of|what kind of|how should we|what are the)\b",
            s,
            re.IGNORECASE,
        ):
            return True
        return False

    def _is_boilerplate_or_filler(self, sentence: str) -> bool:
        """Returns True if the sentence is administrative boilerplate or conversational padding."""
        s_lower = sentence.lower().strip()
        for pat in self.BOILERPLATE_PATTERNS:
            if re.search(pat, s_lower):
                return True
        for pat in self.FILLER_PATTERNS:
            if re.search(pat, s_lower):
                return True
        return False

    def is_high_signal_sentence(self, sent: str) -> bool:
        """
        Information Density Guard: Prunes low-information conversational filler and brief
        dialogue turns. Requires minimum 11 words, non-interrogative, and at least one
        concrete operational/financial entity anchor.
        """
        words = sent.split()
        if len(words) < 11 or sent.strip().endswith("?"):
            return False
        return bool(self.INFO_ANCHORS.search(sent))

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
        cleaned = self._clean_transcript(text)
        cleaned = re.sub(r"\n+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Split on sentence terminals
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'₹])", cleaned)
        sentences: List[str] = []
        for p in parts:
            p_strip = p.strip()
            if len(p_strip) >= 20:  # Skip tiny fragments
                sentences.append(p_strip)
        return sentences

    def analyze_tone(self, sentences: List[str]) -> Dict[str, Any]:
        """
        Computes sentiment percentage breakdown and continuous tone score across sentences
        using FinBERT-Tone INT8 ONNX or fallback FinancialLexicon.
        """
        if not sentences:
            return {
                "positive_pct": 0.0,
                "neutral_pct": 100.0,
                "negative_pct": 0.0,
                "overall": "NEUTRAL",
                "average_tone_score": 0.0,
                "sample_size": 0,
            }

        counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
        tone_scores: List[float] = []
        scored_sentences = [
            s for s in sentences
            if not self._is_boilerplate_or_filler(s) and not self._is_analyst_question(s)
        ]
        if not scored_sentences:
            scored_sentences = sentences

        for s in scored_sentences:
            cleaned = self._clean_sentence(s)
            res = sentiment_engine.analyze(cleaned)
            lbl = getattr(res, "label", "NEUTRAL")
            counts[lbl] = counts.get(lbl, 0) + 1
            tone_scores.append(getattr(res, "tone_score", 0.0))

        total = sum(counts.values()) or 1
        pos_pct = round((counts["POSITIVE"] / total) * 100, 1)
        neu_pct = round((counts["NEUTRAL"] / total) * 100, 1)
        neg_pct = round((counts["NEGATIVE"] / total) * 100, 1)
        avg_tone = round(float(sum(tone_scores) / len(tone_scores)), 3) if tone_scores else 0.0

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
            "average_tone_score": avg_tone,
            "sample_size": len(scored_sentences),
        }

    def calculate_tone_gap(self, mgmt_score: float, qa_score: float) -> Tuple[float, str]:
        """
        Measures tone divergence between Prepared Remarks and Q&A (high-alpha signal).
        A positive gap indicates management tone softened or became cautious under questioning.
        """
        gap = round(mgmt_score - qa_score, 3)
        if gap >= 0.10:
            summary = (
                f"Tone Gap Alert (+{gap:.2f}): Management tone softened during Q&A "
                f"(Opening: {mgmt_score:+.2f} vs Q&A: {qa_score:+.2f})."
            )
        elif gap <= -0.10:
            summary = (
                f"Constructive Q&A Shift ({gap:+.2f}): Management sounded more upbeat during Q&A "
                f"(Opening: {mgmt_score:+.2f} vs Q&A: {qa_score:+.2f})."
            )
        else:
            summary = (
                f"Consistent Tone: Opening remarks and Q&A remained aligned "
                f"(Opening: {mgmt_score:+.2f} vs Q&A: {qa_score:+.2f})."
            )
        return gap, summary

    def compute_hedging_rate(self, text: str) -> float:
        """Computes Loughran-McDonald financial uncertainty density per 100 words."""
        return sentiment_engine.lexicon.compute_uncertainty_rate(text)

    def score_aspects(self, sentences: List[str]) -> Dict[str, float]:
        """
        Calculates topic-level sentiment scores across 4 key financial buckets:
        Demand/Revenue, Margins/Costs, Guidance/Outlook, and CapEx/Debt.
        """
        anchor_bags = {
            topic: set(words.split())
            for topic, words in self.TOPIC_ANCHORS.items()
        }

        topic_scores: Dict[str, List[float]] = {topic: [] for topic in self.TOPIC_ANCHORS}

        for s in sentences:
            if self._is_boilerplate_or_filler(s) or self._is_analyst_question(s):
                continue
            cleaned = self._clean_sentence(s)
            s_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", cleaned.lower()))
            if not s_words:
                continue

            best_topic = None
            max_overlap = 0
            for topic, anchor_words in anchor_bags.items():
                overlap = len(s_words.intersection(anchor_words))
                if overlap > max_overlap and overlap >= 1:
                    max_overlap = overlap
                    best_topic = topic

            if best_topic is not None:
                res = sentiment_engine.analyze(cleaned)
                topic_scores[best_topic].append(res.tone_score)

        return {
            topic: round(float(sum(scores) / len(scores)), 2)
            for topic, scores in topic_scores.items()
            if scores
        }

    def extract_red_flags(self, sentences: List[str], n: int = 3) -> List[Dict[str, Any]]:
        """
        Extracts the top N most cautious or negative verbatim management statements.
        Combines FinBERT tone scoring with Loughran-McDonald uncertainty indicators.
        Enforces Information Density Guard so vague conversational filler is excluded.
        """
        scored_candidates: List[Tuple[float, str]] = []
        high_density_candidates: List[Tuple[float, str]] = []
        for s in sentences:
            cleaned = self._clean_sentence(s)
            if len(cleaned) < 40 or len(cleaned.split()) < 8:
                continue
            if self._is_boilerplate_or_filler(cleaned) or self._is_analyst_question(cleaned):
                continue
            if re.search(r"\b(?:the\s+next\s+one|next\s+question|operator|moderator|take\s+this\s+opportunity)\b", cleaned, re.IGNORECASE):
                continue

            res = sentiment_engine.analyze(cleaned)
            uncertainty_rate = sentiment_engine.lexicon.compute_uncertainty_rate(cleaned)
            # Penalize tone score further if uncertainty words are present
            risk_score = res.tone_score - (0.25 if uncertainty_rate > 0 else 0.0)

            # If a statement is unambiguously positive (tone > 0.15), it is positive forward guidance, not a risk flag
            if res.tone_score < 0.0 or (uncertainty_rate > 0 and res.tone_score <= 0.15):
                scored_candidates.append((risk_score, cleaned))
                if self.is_high_signal_sentence(cleaned):
                    high_density_candidates.append((risk_score, cleaned))

        candidates_to_use = high_density_candidates if high_density_candidates else scored_candidates
        candidates_to_use.sort(key=lambda x: x[0])  # Lowest (most cautious) first
        return [
            {"text": text, "score": round(score, 2)}
            for score, text in candidates_to_use[:n]
        ]

    def mine_guidance_metrics(
        self, text: str, candidate_sentences: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Extracts forward-looking financial targets, Capex plans, margins, and debt metrics.
        """
        results: List[Dict[str, str]] = []
        sentences = candidate_sentences if candidate_sentences is not None else self._split_sentences(text)
        seen_snippets: Set[str] = set()

        for sent in sentences:
            if self._is_boilerplate_or_filler(sent) or self._is_analyst_question(sent):
                continue

            sent_clean = self._clean_sentence(sent)

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

    def extract_top_sentences(
        self, text: str, n: int = 5, candidate_sentences: Optional[List[str]] = None
    ) -> List[str]:
        """
        Extractive Summarization using TF-IDF Graph Centrality with Concrete Statement Scoring.
        Excludes analyst questions and conversational filler. Heavily weights statements containing
        concrete numerical metrics (percentages, capex amounts, margins, capacities).
        """
        raw_sents = candidate_sentences if candidate_sentences is not None else self._split_sentences(text)
        candidates: List[str] = []
        high_density: List[str] = []

        for s in raw_sents:
            cleaned = self._clean_sentence(s)
            if len(cleaned) < 40 or len(cleaned.split()) < 8:
                continue
            if self._is_analyst_question(cleaned) or self._is_boilerplate_or_filler(cleaned):
                continue
            candidates.append(cleaned)
            if self.is_high_signal_sentence(cleaned):
                high_density.append(cleaned)

        if high_density:
            candidates = high_density

        if len(candidates) <= 1:
            return candidates

        word_bags: List[List[str]] = []
        doc_freq: collections.Counter = collections.Counter()
        for sent in candidates:
            words = [
                w.lower()
                for w in re.findall(r"\b[a-zA-Z]{3,}\b", sent)
                if w.lower() not in self.STOP_WORDS
            ]
            word_bags.append(words)
            doc_freq.update(set(words))

        num_docs = len(candidates)

        vectors: List[Dict[str, float]] = []
        for bag in word_bags:
            term_freq = collections.Counter(bag)
            vec: Dict[str, float] = {}
            for word, count in term_freq.items():
                idf = math.log((num_docs + 1) / (doc_freq[word] + 1)) + 1.0
                vec[word] = count * idf
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            vectors.append({w: v / norm for w, v in vec.items()})

        centrality_scores = [0.0] * num_docs
        for i in range(num_docs):
            for j in range(i + 1, num_docs):
                sim = sum(vectors[i].get(w, 0.0) * vectors[j].get(w, 0.0) for w in vectors[i])
                centrality_scores[i] += sim
                centrality_scores[j] += sim

        for i, sent in enumerate(candidates):
            has_metric = bool(
                re.search(
                    r"\b(?:\d+(?:\.\d+)?\s*%|\d+\s*bps|₹|Rs\.?|INR|\$|\bcr\b|\bcrore\b|\blakh\b|\bbn\b|\bmn\b|\bgigawatt\b|\bgwh\b|\bmw\b|\butilization\b)\b",
                    sent,
                    re.IGNORECASE,
                )
            )
            has_biz_term = bool(
                re.search(
                    r"\b(?:revenue|ebitda|margin|margins|growth|pat|profit|capex|investment|pack|segments|breakeven|order book|utilization)\b",
                    sent,
                    re.IGNORECASE,
                )
            )

            if has_metric and has_biz_term:
                centrality_scores[i] = (centrality_scores[i] + 0.5) * 3.0
            elif has_metric or has_biz_term:
                centrality_scores[i] = (centrality_scores[i] + 0.2) * 1.8
            else:
                centrality_scores[i] *= 0.4

        ranked_indices = sorted(range(num_docs), key=lambda idx: centrality_scores[idx], reverse=True)

        selected_indices: List[int] = []
        for idx in ranked_indices:
            # Check for redundancy against already selected candidates
            is_redundant = False
            for sel_idx in selected_indices:
                # 1. Cosine similarity between TF-IDF unit vectors
                cos_sim = sum(
                    vectors[idx].get(w, 0.0) * vectors[sel_idx].get(w, 0.0)
                    for w in vectors[idx]
                )
                if cos_sim >= 0.55:
                    is_redundant = True
                    break

                # 2. Key financial metric & domain topic overlap (e.g. both highlighting "80% utilization")
                idx_metrics = set(
                    re.findall(
                        r"\b\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*(?:gigawatt|gwh|crore|cr|bps|mw)\b",
                        candidates[idx].lower(),
                    )
                )
                sel_metrics = set(
                    re.findall(
                        r"\b\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*(?:gigawatt|gwh|crore|cr|bps|mw)\b",
                        candidates[sel_idx].lower(),
                    )
                )
                if idx_metrics and sel_metrics and idx_metrics.intersection(sel_metrics):
                    idx_nouns = set(word_bags[idx])
                    sel_nouns = set(word_bags[sel_idx])
                    if len(idx_nouns.intersection(sel_nouns)) >= 2:
                        is_redundant = True
                        break

            if not is_redundant:
                selected_indices.append(idx)
                if len(selected_indices) >= n:
                    break

        selected_indices.sort()
        return [candidates[idx] for idx in selected_indices]

    def extract_topics(self, text: str, n: int = 6) -> List[str]:
        """
        Extracts top N salient discussion topics (n-grams) from the concall text.
        Excludes speaker names, company name suffixes, and date/page artifacts.
        """
        speaker_stops = self._extract_speaker_names(text)
        all_stops = self.STOP_WORDS.union(speaker_stops)

        raw_sents = self._split_sentences(text)
        all_bigrams: List[str] = []

        for sent in raw_sents:
            cleaned = self._clean_sentence(sent)
            if self._is_boilerplate_or_filler(cleaned) or self._is_analyst_question(cleaned):
                continue
            if re.search(r"\b(?:the\s+next\s+one|next\s+question|operator|moderator|take\s+this\s+opportunity)\b", cleaned, re.IGNORECASE):
                continue

            words = [
                w.lower()
                for w in re.findall(r"\b[a-zA-Z]{3,}\b", cleaned)
                if w.lower() not in all_stops
            ]
            for i in range(len(words) - 1):
                w1, w2 = words[i], words[i + 1]
                if w1 != w2:
                    all_bigrams.append(f"{w1} {w2}")

        if not all_bigrams:
            return []

        counter = collections.Counter(all_bigrams)
        seen_word_sets: List[Set[str]] = []
        unique_topics: List[str] = []

        for bg, _ in counter.most_common():
            bg_lower = bg.lower()
            if bg_lower in self.THEME_STOP_PHRASES:
                continue
            words_in_bg = bg_lower.split()
            if any(w in {"digit", "digits", "year", "years", "quarter", "quarters", "month", "months"} for w in words_in_bg):
                continue
            if words_in_bg and words_in_bg[0] in {"double", "single", "first", "second", "third", "fourth", "next", "last", "current", "full", "past", "few", "couple"}:
                continue
            w_set = set(words_in_bg)
            if any(w_set == existing for existing in seen_word_sets):
                continue
            seen_word_sets.append(w_set)
            unique_topics.append(bg.title())
            if len(unique_topics) >= n:
                break

        return unique_topics

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Runs full end-to-end non-LLM quantitative concall intelligence analysis.
        Uses automatic speaker discovery to isolate Management remarks from Analyst Q&A.
        """
        speaker_data = self.discover_speakers(text)
        mgmt_sents = speaker_data["mgmt_sentences"]
        mgmt_prepared_sents = speaker_data.get("mgmt_prepared_sentences", [])
        mgmt_qa_sents = speaker_data.get("mgmt_qa_sentences", [])
        qa_sents = speaker_data["analyst_sentences"]

        # Fallback if no speakers were identified (e.g. raw text without speaker tags)
        if not mgmt_sents:
            mgmt_sents, qa_sents = self.segment_transcript(text)
            mgmt_prepared_sents = mgmt_sents
            mgmt_qa_sents = []

        mgmt_tone = self.analyze_tone(mgmt_prepared_sents if mgmt_prepared_sents else mgmt_sents)
        mgmt_qa_tone = self.analyze_tone(mgmt_qa_sents) if mgmt_qa_sents else None
        analyst_tone = self.analyze_tone(qa_sents)

        # Tone divergence compares Prepared Remarks vs Management Q&A Answers (fallback to Analyst Q&A)
        qa_comparison_score = (
            mgmt_qa_tone.get("average_tone_score", 0.0)
            if (mgmt_qa_tone and mgmt_qa_tone.get("sample_size", 0) > 0)
            else analyst_tone.get("average_tone_score", 0.0)
        )
        tone_gap, divergence_summary = self.calculate_tone_gap(
            mgmt_tone.get("average_tone_score", 0.0),
            qa_comparison_score,
        )

        all_substantive_sents = mgmt_sents + qa_sents
        spoken_text = " ".join(all_substantive_sents) if all_substantive_sents else text
        hedge_rate = self.compute_hedging_rate(spoken_text)
        topic_scores = self.score_aspects(all_substantive_sents)

        # Strictly feed management sentences into risk flags, guidance, and takeaways
        target_mgmt = mgmt_sents if mgmt_sents else all_substantive_sents
        red_flags = self.extract_red_flags(target_mgmt, n=3)

        guidance = self.mine_guidance_metrics(text, candidate_sentences=target_mgmt)
        takeaways = self.extract_top_sentences(text, n=5, candidate_sentences=target_mgmt)
        topics = self.extract_topics(text, n=6)

        return {
            "management_tone": mgmt_tone,
            "qa_tone": analyst_tone,
            "tone_gap_alert": tone_gap,
            "tone_divergence_summary": divergence_summary,
            "hedge_rate_per_100w": hedge_rate,
            "topic_sentiment": topic_scores,
            "red_flags": red_flags,
            "guidance_metrics": guidance,
            "top_takeaways": takeaways,
            "key_themes": topics,
            "sentence_count": len(mgmt_sents) + len(qa_sents),
            "discovered_management": speaker_data.get("discovered_management", []),
            "discovered_analysts": speaker_data.get("discovered_analysts", []),
        }


# Global singleton instance
concall_analyzer = ConcallAnalyzer()

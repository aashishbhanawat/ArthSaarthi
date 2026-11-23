import re
from typing import Dict, List, Optional, Set


class RelevanceFilter:
    """
    Stage 1: Noise & Relevance Filter for financial news feeds.
    Drops non-financial articles, exam spam, crime, sports, entertainment,
    and disambiguates short ticker collisions (e.g. SCI = Supreme Court vs Shipping Corp).
    """

    # Educational / Government / Exam spam
    EXAM_PATTERNS = [
        r"\banswer\s*key\b", r"\badmit\s*card\b", r"\bhall\s*ticket\b",
        r"\bprovisional\s*answer\b", r"\bcut[\s-]*off\b", r"\bsyllabus\b",
        r"\brecruitment\b", r"\bcivil\s*judge\b", r"\bcourt\s*assistant\b",
        r"\bapply\s*online\b", r"\bexam\s*date\b", r"\bboard\s*exam\b",
        r"\bresult\s*declared\b", r"\bscholarship\b", r"\badmissions?\b",
        r"\bvacanc(y|ies)\b", r"\bselection\s*list\b", r"\bcounselling\b",
        r"\bjca\b", r"\bquestion\s*paper\b", r"\bmodel\s*paper\b",
        r"\b\w+\.gov\.in\b", r"\b\w+\.nic\.in\b",
    ]

    # Non-business general news noise (crime, sports, entertainment, space)
    GENERAL_NOISE_PATTERNS = [
        r"\brape\b", r"\bmurder\b", r"\bassault\b", r"\bkidnap\w*\b",
        r"\barrested\s*for\b", r"\bhoroscope\b", r"\bastrology\b",
        r"\bweather\s*forecast\b", r"\bcyclone\b", r"\bearthquake\b",
        r"\bbollywood\b", r"\bbox\s*office\b", r"\btrailer\b",
        r"\bcricket\b", r"\bipl\b", r"\btest\s*match\b", r"\bt20\b",
        r"\bchampions\s*league\b", r"\bpremier\s*league\b", r"\bfootball\b",
        r"\bworld\s*cup\b", r"\bebola\b", r"\bvoyager\s*[12]\b",
        r"\bnasa\b", r"\bmars\s*rover\b", r"\bspace\s*probe\b",
        r"\bcelebrity\b", r"\bdating\b", r"\bactress\b", r"\bactor\b",
    ]

    # Positive financial & corporate business signals
    FINANCIAL_KEYWORDS: Set[str] = {
        # Equity & Markets
        "share", "shares", "stock", "stocks", "equity", "equities", "nse", "bse",
        "sensex", "nifty", "market", "markets", "ipo", "fpo", "dividend", "dividends",
        "bonus", "split", "buyback", "promoter", "promoters", "stake", "valuation",
        "trading", "trader", "traders", "investor", "investors", "broker", "brokerage",
        "brokerages", "target", "sebi",
        # Corporate Financials
        "profit", "profits", "revenue", "revenues", "earnings", "ebitda", "pat",
        "margin", "margins", "guidance", "turnover", "debt", "capex", "quarter",
        "quarterly", "concall", "results", "q1", "q2", "q3", "q4", "fy24", "fy25",
        "fy26", "fy27", "annual report", "financial results",
        # Economy & Commodities
        "rbi", "repo", "inflation", "gdp", "crude", "oil", "gold", "silver", "mcx",
        "rupee", "dollar", "forex", "treasury", "bond", "bonds", "yield", "economy",
        "economic", "fiscal", "banking", "bank", "banks", "lending", "nbfc", "realty",
        "housing", "merger", "acquisition", "order book", "contracts", "tender",
    }

    # Ticker-specific collision disambiguation rules
    TICKER_COLLISIONS: Dict[str, Dict[str, List[str]]] = {
        "SCI": {
            # Disallow Supreme Court of India & Science news
            "reject": [
                r"\bsupreme\s*court\b", r"\bjunior\s*court\b", r"\bsci\.gov\.in\b",
                r"\bhigh\s*court\b", r"\bjudge\b", r"\bcourt\s*assistant\b",
                r"\bjudiciary\b", r"\blawyer\b", r"\bbench\b", r"\badvocate\b",
                r"\bscience\b", r"\bscientist\b", r"\bscientific\b", r"\bjca\b",
            ],
            # Allow Shipping Corporation of India
            "require_any": [
                "shipping", "ship", "ships", "vessel", "vessels", "fleet", "psu",
                "dividend", "shares", "stock", "profit", "results", "target",
                "q1", "q2", "q3", "q4", "nse", "bse",
            ],
        },
        "IT": {
            "reject": [r"\binformation\s*technology\b", r"\bincome\s*tax\b"],
            "require_any": ["shares", "stock", "nse", "bse", "target", "profit"],
        },
        "IDEA": {
            "reject": [r"\bgood\s*idea\b", r"\bno\s*idea\b", r"\bnew\s*idea\b", r"\ban\s*idea\b"],
            "require_any": ["vodafone", "telecom", "vi", "agr", "shares", "stock", "subscriber"],
        },
        "CARE": {
            "reject": [r"\bhealth\s*care\b", r"\bchild\s*care\b", r"\btake\s*care\b", r"\bday\s*care\b", r"\bintensive\s*care\b"],
            "require_any": ["ratings", "credit rating", "shares", "stock", "downgrade", "upgrade"],
        },
        "FACT": {
            "reject": [r"\bin\s*fact\b", r"\bfact\s*check\b", r"\bmatter\s*of\s*fact\b", r"\bhard\s*facts?\b"],
            "require_any": ["fertiliser", "fertilizer", "chemicals", "psu", "shares", "stock"],
        },
        "OIL": {
            "reject": [],
            "require_any": ["oil india", "crude", "drilling", "psu", "dividend", "shares", "stock", "exploration"],
        },
        "REC": {
            "reject": [r"\brec\s*room\b", r"\brec\s*center\b", r"\brecreation\b"],
            "require_any": ["power", "lending", "nbfc", "shares", "stock", "dividend", "target", "profit", "rural electrification"],
        },
        "LT": {
            "reject": [r"\blt\.\s+[a-z]+\b", r"\blieutenant\b"],
            "require_any": ["larsen", "toubro", "infrastructure", "construction", "order", "shares", "stock", "q1", "q2", "q3", "q4"],
        },
    }

    def is_noise(self, title: str, summary: Optional[str] = None) -> bool:
        """Returns True if the text matches non-financial noise signatures."""
        full_text = f"{title} {summary or ''}".lower()

        # Check Exam & Government Recruitment spam
        for pattern in self.EXAM_PATTERNS:
            if re.search(pattern, full_text):
                return True

        # Check General Non-Business Noise (crime, sports, gossip, space)
        for pattern in self.GENERAL_NOISE_PATTERNS:
            if re.search(pattern, full_text):
                return True

        return False

    def is_financial_relevant(self, title: str, summary: Optional[str] = None, category: str = "NEWS") -> bool:
        """
        Evaluates whether an article has genuine financial market or economic relevance.
        Broker reports and concalls are inherently relevant.
        """
        if category in ["BROKER_REPORT", "CONCALL"]:
            return not self.is_noise(title, summary)

        if self.is_noise(title, summary):
            return False

        full_text = f"{title} {summary or ''}".lower()
        words = set(re.findall(r"\b[a-zA-Z0-9-]+\b", full_text))
        financial_matches = words.intersection(self.FINANCIAL_KEYWORDS)

        # Requires at least one verified financial signal
        return len(financial_matches) >= 1

    def validate_ticker(self, symbol: str, title: str, summary: Optional[str] = None) -> bool:
        """
        Disambiguates short or common-word tickers (e.g. SCI, IT, IDEA, CARE, FACT, REC, LT).
        Returns False if the context indicates a collision with a non-company acronym.
        """
        clean_sym = symbol.upper().strip()
        rule = self.TICKER_COLLISIONS.get(clean_sym)
        if not rule:
            # Long tickers (e.g. RELIANCE, TATAMOTORS, HDFCBANK) have negligible false positive rates
            return True

        full_text = f"{title} {summary or ''}".lower()

        # Check reject patterns
        for reject_pat in rule.get("reject", []):
            if re.search(reject_pat, full_text):
                return False

        # Check required co-occurring financial or company markers
        require_any = rule.get("require_any", [])
        if require_any:
            has_required = False
            for req in require_any:
                pattern = r"\b" + re.escape(req) + r"\b"
                if re.search(pattern, full_text):
                    has_required = True
                    break
            if not has_required:
                return False

        return True


# Global relevance filter singleton
relevance_filter = RelevanceFilter()

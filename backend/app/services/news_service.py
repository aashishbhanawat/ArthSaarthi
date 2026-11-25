import email.utils
import hashlib
import html
import logging
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import httpx
from sqlalchemy.orm import Session

from app.crud.crud_news import market_news
from app.ml.deduplicator import headline_deduplicator
from app.ml.entity_matcher import FastEntityMatcher
from app.ml.relevance_filter import relevance_filter
from app.ml.sentiment_engine import sentiment_engine
from app.models.asset import Asset
from app.models.transaction import Transaction
from app.models.watchlist import WatchlistItem
from app.schemas.market_news import MarketNewsArticleCreate

logger = logging.getLogger(__name__)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# General & Exchange RSS feeds
FEED_CONFIGS = [
    # --- Macro & Financial Market News ---
    {
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "source": "The Economic Times",
        "category": "NEWS",
    },
    {
        "url": "https://www.moneycontrol.com/rss/MCtopnews.xml",
        "source": "Moneycontrol",
        "category": "NEWS",
    },
    {
        "url": "https://www.livemint.com/rss/markets",
        "source": "Livemint Markets",
        "category": "NEWS",
    },
    {
        "url": "https://www.livemint.com/rss/companies",
        "source": "Livemint Companies",
        "category": "NEWS",
    },
    # --- Institutional Broker Reports & Target Prices ---
    {
        "url": "https://www.moneycontrol.com/rss/brokeragereports.xml",
        "source": "Moneycontrol Research",
        "category": "BROKER_REPORT",
    },
    # --- Concalls & Earnings Podcasts ---
    {
        "url": "https://trendlyne.com/feeds/earning-calls-podcast-rss/",
        "source": "Trendlyne Concalls",
        "category": "CONCALL",
    },
    # --- Quarterly Results & Financial Disclosures ---
    {
        "url": "https://www.moneycontrol.com/rss/results.xml",
        "source": "Moneycontrol Results",
        "category": "RESULT",
    },
    {
        "url": "https://nsearchives.nseindia.com/content/RSS/Financial_Results.xml",
        "source": "NSE Results",
        "category": "RESULT",
    },
    # --- Official Exchange Corporate Disclosures & Actions (NSE & BSE) ---
    {
        "url": "https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml",
        "source": "NSE Announcements",
        "category": "NEWS",
    },
    {
        "url": "https://nsearchives.nseindia.com/content/RSS/Corporate_action.xml",
        "source": "NSE Corporate Actions",
        "category": "NEWS",
    },
    {
        "url": "https://www.bseindia.com/data/xml/announcements.aspx",
        "source": "BSE Announcements",
        "category": "NEWS",
        "max_items": 100,
    },
    {
        "url": "https://www.bseindia.com/data/XML/CorpActionFeed.aspx",
        "source": "BSE Corporate Actions",
        "category": "NEWS",
    },
]

POSITIVE_KEYWORDS = {
    "profit", "growth", "surge", "surges", "jump", "jumps", "gain", "gains",
    "rally", "record", "beat", "beats", "upgrade", "upgrades", "buy", "higher",
    "bullish", "rise", "rises", "expansion", "dividend", "bonus", "order win",
    "strong", "outperform", "accumulate", "upside", "milestone",
}

NEGATIVE_KEYWORDS = {
    "loss", "losses", "drop", "drops", "fall", "falls", "slump", "slumps",
    "decline", "declines", "miss", "misses", "downgrade", "downgrades", "sell",
    "reduce", "cut", "cuts", "bearish", "plunge", "plunges", "penalty", "fraud",
    "crash", "debt", "warning", "weak", "downside", "investigation",
}

GENERIC_NAME_BLACKLIST = {
    "general insurance", "life insurance", "health insurance", "insurance company",
    "corporation of india", "bank of india", "state bank", "central bank", "union bank",
    "finance corporation", "development finance", "industries", "enterprises",
    "holdings", "services", "solutions", "technologies", "international",
    "global", "power", "energy", "infrastructure", "steel", "cement", "pharma",
    "chemicals", "petrochemicals", "securities", "capital", "ventures",
    "commercial", "industrial", "financial services", "financial",
    "stock", "equity", "share", "shares", "oil and gas", "oil & gas",
}


def clean_html_text(text: Optional[str]) -> str:
    """Strips HTML tags and unescapes entities."""
    if not text:
        return ""
    stripped = re.sub(r"<[^>]+>", " ", text)
    unescaped = html.unescape(stripped)
    return " ".join(unescaped.split())


def calculate_sentiment(text: str) -> str:
    """Computes financial sentiment using the centralized sentiment engine (FinBERT or Lexicon)."""
    return sentiment_engine.analyze(text).label


def parse_rfc2822_date(date_str: Optional[str]) -> datetime:
    """Parses RFC-2822, ISO, or Indian Exchange date string into timezone-aware UTC datetime."""
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        # NSE & BSE timestamp format: "22-Nov-2026 14:39:18" (IST / Asia/Kolkata UTC+05:30)
        dt = datetime.strptime(date_str.strip(), "%d-%b-%Y %H:%M:%S")
        ist = timezone(timedelta(hours=5, minutes=30))
        return dt.replace(tzinfo=ist).astimezone(timezone.utc)
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def extract_broker_metadata(title: str, summary: str) -> Dict[str, Any]:
    """
    Extracts recommendation, target price, and broker name from typical broker reports:
    e.g. 'Buy REC; target of Rs 600: Motilal Oswal'
    """
    meta: Dict[str, Any] = {}
    combined = f"{title} {summary}"

    # Recommendation
    rec_match = re.search(r"\b(BUY|ACCUMULATE|HOLD|REDUCE|SELL|NEUTRAL)\b", title, re.IGNORECASE)
    if rec_match:
        meta["recommendation"] = rec_match.group(1).upper()
    else:
        meta["recommendation"] = "BUY" if "target of" in title.lower() else "NEUTRAL"

    # Target price
    tp_match = re.search(r"target\s*(?:of|price)?\s*(?:rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)", combined, re.IGNORECASE)
    if tp_match:
        try:
            meta["target_price"] = float(tp_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Broker name (after colon or 'by')
    broker_match = re.search(r":\s*([A-Za-z\s]+?)(?:\s*-\s*|\.|$)", title)
    if broker_match:
        meta["broker"] = broker_match.group(1).strip()
    else:
        by_match = re.search(r"\bby\s+([A-Za-z\s]+?)(?:\s*-\s*|\.|$)", title, re.IGNORECASE)
        if by_match:
            meta["broker"] = by_match.group(1).strip()

    return meta


def extract_concall_metadata(
    title: str,
    summary: str,
    enclosure_url: Optional[str],
    url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extracts quarter, concall audio link, and transcript metadata.
    e.g. 'REC Limited - Q2 FY25 Earnings Call Podcast' or BSE/NSE transcript attachments.
    """
    meta: Dict[str, Any] = {}
    target_link = enclosure_url or url
    if target_link:
        lower_link = target_link.lower()
        if lower_link.endswith(".pdf") or "corpfiling" in lower_link or "transcript" in lower_link:
            meta["transcript_url"] = target_link
        else:
            meta["audio_url"] = target_link

    quarter_match = re.search(r"\b(Q[1-4]\s*(?:FY\s*\d{2,4}|\d{4})?)\b", title, re.IGNORECASE)
    if quarter_match:
        meta["quarter"] = quarter_match.group(1).upper()

    return meta


MONTH_NAME_TO_NUM = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _fiscal_quarter_from_month_year(month: int, yr: int) -> Optional[str]:
    """Helper to convert calendar month and year to Indian fiscal quarter (April 1 to March 31)."""
    if yr < 100:
        yr += 2000
    if month in [4, 5, 6]:
        return f"Q1 FY{str(yr + 1)[-2:]}"
    elif month in [7, 8, 9]:
        return f"Q2 FY{str(yr + 1)[-2:]}"
    elif month in [10, 11, 12]:
        return f"Q3 FY{str(yr + 1)[-2:]}"
    elif month in [1, 2, 3]:
        return f"Q4 FY{str(yr)[-2:]}"
    return None


def extract_quarter_from_text(text: str) -> Optional[str]:
    """
    Extracts financial reporting quarter from text (e.g. 'Q2 FY27', 'Q2FY25',
    or date-based reporting like 'ended 30.09.2026' or 'ended 30th September, 2026' -> 'Q2 FY27').
    """
    if not text:
        return None
    # 1. Explicit Q1-Q4 / FYXX patterns
    q_match = re.search(r"\b(Q[1-4]\s*(?:FY\s*\d{2,4}|\d{4})?)\b", text, re.IGNORECASE)
    if q_match:
        return q_match.group(1).upper()

    # 2. Date-based quarter inference for Indian reporting (April 1 to March 31 fiscal year)
    # A: Numerical date: ended 30.09.2026 or 30/09/2026 or 30-09-2026
    num_date_match = re.search(
        r"(?:quarter|half\s*year|year)\s*ended\s*[-–—:]?\s*([0-3]?[0-9])[./-]([0-1]?[0-9])[./-](\d{2,4})",
        text,
        re.IGNORECASE,
    )
    if num_date_match:
        try:
            month = int(num_date_match.group(2))
            yr = int(num_date_match.group(3))
            return _fiscal_quarter_from_month_year(month, yr)
        except (ValueError, TypeError):
            pass

    # B: Word date: ended 30th September, 2026
    word_date_match = re.search(
        r"(?:quarter|half\s*year|year)\s*ended\s*[-–—:]?\s*(?:on\s*)?(?:([0-3]?[0-9])(?:st|nd|rd|th)?\s+)?([A-Za-z]+)[,\s]+(\d{2,4})",
        text,
        re.IGNORECASE,
    )
    if word_date_match:
        m_name = word_date_match.group(2).lower()[:3]
        if m_name in MONTH_NAME_TO_NUM:
            try:
                month = MONTH_NAME_TO_NUM[m_name]
                yr = int(word_date_match.group(3))
                return _fiscal_quarter_from_month_year(month, yr)
            except (ValueError, TypeError):
                pass

    # C: Inverted word date: ended September 30, 2026
    inv_date_match = re.search(
        r"(?:quarter|half\s*year|year)\s*ended\s*[-–—:]?\s*(?:on\s*)?([A-Za-z]+)\s+([0-3]?[0-9])(?:st|nd|rd|th)?[,\s]+(\d{2,4})",
        text,
        re.IGNORECASE,
    )
    if inv_date_match:
        m_name = inv_date_match.group(1).lower()[:3]
        if m_name in MONTH_NAME_TO_NUM:
            try:
                month = MONTH_NAME_TO_NUM[m_name]
                yr = int(inv_date_match.group(3))
                return _fiscal_quarter_from_month_year(month, yr)
            except (ValueError, TypeError):
                pass

    return None


def extract_corporate_metadata(
    title: str, summary: str, is_exchange_filing: bool = False
) -> Dict[str, Any]:
    """
    Extracts structured metadata for corporate actions (dividends, splits, bonuses, buybacks)
    and major corporate governance changes (leadership changes, order wins, credit ratings).
    Excludes editorial yield/screening news from being falsely tagged as dividend corporate actions.
    """
    meta: Dict[str, Any] = {}
    full = f"{title} {summary}"

    # Check for general editorial dividend screening/yield articles
    is_editorial_yield = bool(
        re.search(
            r"\b(?:dividend\s+yield|dividend\s+income|attractive\s+dividend|dividend\s+stocks?|dividend\s+picks?|stocks?\s+with\s+.*dividend|high\s+dividend\s+yield)\b",
            full,
            re.IGNORECASE,
        )
    )
    has_div_declaration = bool(
        re.search(
            r"\b(?:interim\s+dividend|final\s+dividend|special\s+dividend|"
            r"declared\s+dividend|declare\s+dividend|declaration\s+of\s+dividend|"
            r"recommended\s+dividend|recommends\s+dividend|"
            r"approved\s+dividend|approves\s+dividend|board\s+approves\s+dividend|"
            r"dividend\s+of\s+(?:rs|inr|₹)|dividend\s*:\s*(?:rs|inr|₹)?\s*[\d.]+|"
            r"purpose\s*:\s*dividend|purpose\s*[-–—:]\s*dividend|"
            r"record\s+date\s+for\s+dividend|ex-dividend\s+date)\b",
            full,
            re.IGNORECASE,
        )
    )

    # 1. Dividend
    if (has_div_declaration or (is_exchange_filing and re.search(r"\bdividend\b", full, re.IGNORECASE))) and not (
        is_editorial_yield and not has_div_declaration
    ):
        meta["action_type"] = "DIVIDEND"
        div_match = re.search(
            r"(?:dividend\s*(?:of)?\s*[-–—:]?\s*(?:re\.?|rs\.?|inr|₹)?\s*([\d.]+)|(?:re\.?|rs\.?|inr|₹)\s*([\d.]+)\s*(?:/-)?\s*per\s*share)",
            full,
            re.IGNORECASE,
        )
        if div_match:
            try:
                amt_str = div_match.group(1) or div_match.group(2)
                meta["dividend_amount"] = float(amt_str)
            except (ValueError, TypeError):
                pass
    # 2. Stock Split
    elif re.search(r"\b(?:face\s*value\s*split|sub-division|sub\s*division|stock\s*split)\b", full, re.IGNORECASE):
        meta["action_type"] = "SPLIT"
    # 3. Bonus Issue
    elif re.search(r"\bbonus\s*(?:issue|shares)\b", full, re.IGNORECASE):
        meta["action_type"] = "BONUS"
    # 4. Buyback
    elif re.search(r"\bbuy\s*back\b", full, re.IGNORECASE):
        meta["action_type"] = "BUYBACK"
    # 5. Rights Issue
    elif re.search(r"\brights\s*issue\b", full, re.IGNORECASE):
        meta["action_type"] = "RIGHTS"

    # Ex-Date & Record Date
    ex_match = re.search(
        r"ex[- ]?date\s*:\s*([0-9]{1,2}[- ][A-Za-z]{3}[- ][0-9]{2,4}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{4})",
        full,
        re.IGNORECASE,
    )
    if ex_match:
        meta["ex_date"] = ex_match.group(1).strip()

    rd_match = re.search(
        r"record\s*date\s*:\s*([0-9]{1,2}[- ][A-Za-z]{3}[- ][0-9]{2,4}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{4})",
        full,
        re.IGNORECASE,
    )
    if rd_match:
        meta["record_date"] = rd_match.group(1).strip()

    # 6. Management / Governance Changes
    if re.search(
        r"\b(?:appointment|resignation|cessation)\s+of\s+(?:.*?\b)?(?:director|managing\s+director|md|ceo|chief\s+executive|cfo|chief\s+financial|auditor|company\s+secretary|kmp)\b",
        full,
        re.IGNORECASE,
    ):
        meta["change_type"] = "MANAGEMENT_CHANGE"
    # 7. Order Win / Commercial Capacity Expansion
    elif re.search(
        r"\b(?:order\s*win|bagged\s*order|contract\s*award|commercial\s*production|capacity\s*expansion|new\s*plant|commissioning)\b",
        full,
        re.IGNORECASE,
    ):
        meta["change_type"] = "ORDER_WIN"
    # 8. Credit Rating
    elif re.search(r"\b(?:credit\s*rating|rating\s*upgrade|rating\s*downgrade|crisil|care\s*ratings?|icra|ind-ra)\b", full, re.IGNORECASE):
        meta["change_type"] = "CREDIT_RATING"

    # 9. Quarter extraction for results
    q_str = extract_quarter_from_text(full)
    if q_str:
        meta["quarter"] = q_str

    return meta


def _is_generic_exchange_description(desc: str) -> bool:
    """Returns True if the exchange description is opaque placeholder text."""
    d = desc.lower().strip()
    if len(d) < 35:
        return True
    generic_patterns = [
        r"^please find enclosed",
        r"^enclosed herewith",
        r"^attached herewith",
        r"^we are enclosing",
        r"^submission of",
        r"^regulation 30",
        r"^disclosure under regulation",
        r"^intimation under regulation",
    ]
    return any(re.search(pat, d) for pat in generic_patterns)


def peek_pdf_subject(pdf_url: str, client: Optional[httpx.Client] = None) -> Optional[str]:
    """
    Downloads and inspects Page 1 of a statutory PDF filing to extract the formal SEBI 'Sub:' line
    when exchange descriptions are generic boilerplate (e.g. 'Please find enclosed.').
    """
    try:
        import io
        import pdfplumber

        c = client or httpx.Client(timeout=6.0, follow_redirects=True, headers=BROWSER_HEADERS)
        resp = c.get(pdf_url)
        if resp.status_code == 200:
            with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                if pdf.pages:
                    p0 = pdf.pages[0].extract_text() or ""
                    m = re.search(r"(?:Sub|Subject)\s*:\s*([^\n\r]+(?:\n[^\n\r]+)?)", p0, re.IGNORECASE)
                    if m:
                        clean_sub = " ".join(m.group(1).split())
                        # Strip standard regulatory prefix
                        clean_sub = re.sub(
                            r"^(?:Disclosure\s+under\s+)?Regulation\s+30\s+(?:of\s+the\s+SEBI\s*\([^)]*\)\s*Regulations,?\s*\d{4}\s*)?[-–—:]\s*",
                            "",
                            clean_sub,
                            flags=re.IGNORECASE,
                        ).strip()
                        return clean_sub[:300]
    except Exception as e:
        logger.debug("Failed to peek PDF subject for %s: %s", pdf_url, e)
    return None


def is_xbrl_stub(title: str, summary: str, url: str) -> bool:
    """Detects if an announcement is an exchange XBRL compliance filing."""
    full = f"{title} {summary}"
    return bool(
        re.search(r"\b(?:para\s+[a-z]-xbrl|xbrl)\b", full, re.IGNORECASE)
        or url.lower().endswith(".xml")
    )


def extract_core_exchange_subject(title: str, summary: str) -> str:
    """Normalizes the core regulatory subject from an exchange disclosure."""
    full = f"{title} {summary}"
    # Remove scrip code in parentheses, e.g. (532134)
    cleaned = re.sub(r"\(\d+\)", " ", full)
    # Remove statutory boilerplate phrases and generic exchange category markers
    cleaned = re.sub(
        r"(?i)\b(?:has informed the exchange about|disclosure under regulation\s*\d+|para\s*[a-z]-xbrl|xbrl|general\s*updates?|updates?|intimation|regarding|subject:)\b",
        " ",
        cleaned,
    )
    cleaned = re.sub(r"[^\w\s]", " ", cleaned).lower()
    return " ".join(cleaned.split())


def are_exchange_subjects_similar(sub1: str, sub2: str) -> bool:
    """Returns True if two exchange subjects describe the exact same event."""
    words1 = [w[:5] for w in sub1.split() if len(w) >= 3 and w not in {"the", "and", "for", "with"}]
    words2 = [w[:5] for w in sub2.split() if len(w) >= 3 and w not in {"the", "and", "for", "with"}]
    if not words1 or not words2:
        return False
    s1, s2 = set(words1), set(words2)
    overlap = len(s1 & s2)
    min_len = min(len(s1), len(s2))
    return min_len > 0 and (overlap / min_len) >= 0.5


def _find_elem(node: ET.Element, *tags: str) -> Optional[ET.Element]:
    """Helper to find first matching child element (Element with no children evaluates to False in bool context)."""
    for tag in tags:
        el = node.find(tag)
        if el is not None:
            return el
    return None


def parse_rss_xml(xml_content: str, default_source: str, default_category: str) -> List[Dict[str, Any]]:
    """
    Parses RSS 2.0 / Atom XML into normalized item dictionaries.
    Handles CDATA, enclosures, and various date/content tags.
    """
    items: List[Dict[str, Any]] = []
    try:
        cleaned_xml = xml_content.strip()
        root = ET.fromstring(cleaned_xml)
    except ET.ParseError as e:
        logger.warning("Failed to parse RSS XML (%s): %s", default_source, e)
        return items

    channel = root.find("channel")
    item_nodes = channel.findall("item") if channel is not None else root.findall(".//item")
    if not item_nodes:
        # Atom feed fallback
        item_nodes = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    for node in item_nodes:
        title_elem = _find_elem(node, "title", "{http://www.w3.org/2005/Atom}title")
        link_elem = _find_elem(node, "link", "{http://www.w3.org/2005/Atom}link")
        desc_elem = _find_elem(
            node,
            "description",
            "{http://www.w3.org/2005/Atom}summary",
            "{http://www.w3.org/2005/Atom}content",
        )
        pub_elem = _find_elem(
            node,
            "pubDate",
            "{http://www.w3.org/2005/Atom}published",
            "{http://www.w3.org/2005/Atom}updated",
        )
        enclosure = node.find("enclosure")

        title = clean_html_text(title_elem.text if title_elem is not None else "")
        if not title:
            continue

        link = ""
        if link_elem is not None:
            link = link_elem.text or link_elem.get("href", "") or ""
        link = link.strip()
        if not link:
            continue

        summary = clean_html_text(desc_elem.text if desc_elem is not None else "")
        pub_date = parse_rfc2822_date(pub_elem.text if pub_elem is not None else None)
        enclosure_url = enclosure.get("url") if enclosure is not None else None

        items.append({
            "title": title,
            "url": link,
            "summary": summary,
            "published_at": pub_date,
            "source": default_source,
            "category": default_category,
            "enclosure_url": enclosure_url,
        })

    return items


class MarketNewsService:
    def __init__(self, client: Optional[httpx.Client] = None, timeout: float = 12.0):
        self.client = client
        self.timeout = timeout

    def _get_client(self) -> httpx.Client:
        if self.client:
            return self.client
        return httpx.Client(headers=BROWSER_HEADERS, timeout=self.timeout, follow_redirects=True)

    def get_active_portfolio_symbols(self, db: Session) -> Set[str]:
        """
        Gathers distinct ticker symbols from all active stock/ETF holdings
        and user watchlists.
        """
        symbols: Set[str] = set()

        # 1. From transactions & assets
        asset_symbols = (
            db.query(Asset.ticker_symbol)
            .join(Transaction, Transaction.asset_id == Asset.id)
            .filter(Asset.asset_type.in_(["STOCK", "ETF", "FOREIGN_STOCK"]))
            .distinct()
            .all()
        )
        for row in asset_symbols:
            if row[0]:
                clean_sym = row[0].split(".")[0].upper().strip()
                if clean_sym:
                    symbols.add(clean_sym)

        # 2. From watchlists
        watchlist_symbols = (
            db.query(Asset.ticker_symbol)
            .join(WatchlistItem, WatchlistItem.asset_id == Asset.id)
            .filter(Asset.asset_type.in_(["STOCK", "ETF", "FOREIGN_STOCK"]))
            .distinct()
            .all()
        )
        for row in watchlist_symbols:
            if row[0]:
                clean_sym = row[0].split(".")[0].upper().strip()
                if clean_sym:
                    symbols.add(clean_sym)

        return symbols

    def get_symbol_keyword_mappings(self, db: Session) -> Dict[str, str]:
        """
        Gathers search keywords (ticker symbols and clean company names)
        mapped to their canonical ticker symbol for all active holdings and watchlists.
        """
        mappings: Dict[str, str] = {}

        # 1. From transactions & assets
        holdings = (
            db.query(Asset.ticker_symbol, Asset.name)
            .join(Transaction, Transaction.asset_id == Asset.id)
            .filter(Asset.asset_type.in_(["STOCK", "ETF", "FOREIGN_STOCK"]))
            .distinct()
            .all()
        )
        # 2. From watchlists
        watchlists = (
            db.query(Asset.ticker_symbol, Asset.name)
            .join(WatchlistItem, WatchlistItem.asset_id == Asset.id)
            .filter(Asset.asset_type.in_(["STOCK", "ETF", "FOREIGN_STOCK"]))
            .distinct()
            .all()
        )

        for row in list(holdings) + list(watchlists):
            ticker_raw, name_raw = row[0], row[1]
            if not ticker_raw:
                continue
            clean_ticker = ticker_raw.split(".")[0].upper().strip()
            if not clean_ticker:
                continue
            mappings[clean_ticker] = clean_ticker

            if name_raw:
                clean_name = name_raw.strip()
                if len(clean_name) >= 4 and clean_name.lower() not in GENERIC_NAME_BLACKLIST:
                    mappings[clean_name] = clean_ticker
                stripped = re.sub(
                    r"\s+(Limited|Ltd\.?|Corporation|Corp\.?|India)\b.*",
                    "",
                    clean_name,
                    flags=re.IGNORECASE,
                ).strip()
                if len(stripped) >= 4 and stripped.lower() not in GENERIC_NAME_BLACKLIST:
                    mappings[stripped] = clean_ticker

            # Special high-precision company aliases
            if clean_ticker == "GICRE":
                mappings["GIC Re"] = "GICRE"
                mappings["GIC RE"] = "GICRE"
                mappings["General Insurance Corporation of India"] = "GICRE"
                mappings.pop("General Insurance", None)
            elif clean_ticker == "HGS":
                mappings["Hinduja Global Solutions"] = "HGS"
                mappings.pop("HGS India", None)

        return mappings

    def match_symbols(
        self, text: str, symbols_or_mappings: Union[Set[str], Dict[str, str]]
    ) -> List[str]:
        """
        Matches active portfolio symbols and company names against title and summary text
        using pure-Python trie entity matcher for deterministic, fast matching.
        Disambiguates short tickers against false collisions.
        """
        if not text or not symbols_or_mappings:
            return []
        matcher = FastEntityMatcher(case_sensitive=False)
        if isinstance(symbols_or_mappings, dict):
            for kw, sym in symbols_or_mappings.items():
                if kw.lower() not in GENERIC_NAME_BLACKLIST:
                    matcher.add_keyword(kw, clean_name=sym)
        else:
            for sym in symbols_or_mappings:
                matcher.add_keyword(sym, clean_name=sym)
        candidates = matcher.extract_keywords(text)
        return [sym for sym in candidates if relevance_filter.validate_ticker(sym, text)]

    def fetch_feed_items(self, feed_url: str, source: str, category: str) -> List[Dict[str, Any]]:
        """Fetches and parses a single RSS feed endpoint."""
        client = self._get_client()
        try:
            resp = client.get(feed_url)
            if resp.status_code == 200:
                return parse_rss_xml(resp.text, default_source=source, default_category=category)
            logger.warning("Feed %s returned status %d", feed_url, resp.status_code)
        except Exception as e:
            logger.warning("Error fetching feed %s: %s", feed_url, e)
        return []

    def _clean_search_term(self, symbol: str, company_name: Optional[str] = None) -> str:
        """Resolves a clean company name or ticker symbol for targeted RSS search queries."""
        if company_name and len(company_name) >= 5 and company_name.upper() != symbol:
            clean_company = re.sub(
                r"\s+(Limited|Ltd\.?|Corporation|Corp\.?|India)\b.*",
                "",
                company_name,
                flags=re.IGNORECASE,
            ).strip()
            if clean_company.lower() in GENERIC_NAME_BLACKLIST or len(clean_company) < 4:
                clean_company = company_name
            return clean_company
        return symbol

    def fetch_google_news_for_symbol(
        self, symbol: str, company_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches targeted Google News RSS for a specific equity ticker.
        Uses full company name where available to avoid false matches against unrelated SME IPOs
        or short ticker acronym collisions, and searches for business developments rather than SEO quote pages.
        """
        term = self._clean_search_term(symbol, company_name)
        if term != symbol:
            query = f'"{term}" (results OR earnings OR business OR shares OR stock)'
        else:
            query = f'"{symbol}" NSE (results OR earnings OR business OR shares OR order)'

        encoded_q = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-IN&gl=IN&ceid=IN:en"
        return self.fetch_feed_items(url, source="Google News", category="NEWS")

    def fetch_broker_research_for_symbol(
        self, symbol: str, company_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches targeted broker research reports and target-price updates via Google News RSS.
        """
        term = self._clean_search_term(symbol, company_name)
        query = (
            f'"{term}" ("broker research" OR "brokerage" OR "target price" '
            f'OR "buy rating" OR "sell rating" OR "Motilal Oswal" OR "ICICI Direct" '
            f'OR "Kotak" OR "JM Financial" OR "Nuvama")'
        )
        encoded_q = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-IN&gl=IN&ceid=IN:en"
        return self.fetch_feed_items(url, source="Google News Research", category="BROKER_REPORT")

    def fetch_yahoo_finance_rss(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Fetches headline news from Yahoo Finance RSS in batches of up to 10 NSE tickers (.NS).
        """
        if not symbols:
            return []
        all_items: List[Dict[str, Any]] = []
        clean_syms = [f"{s.split('.')[0].upper().strip()}.NS" for s in symbols if s]
        for i in range(0, len(clean_syms), 10):
            batch = ",".join(clean_syms[i:i + 10])
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={urllib.parse.quote(batch)}&region=IN&lang=en-IN"
            items = self.fetch_feed_items(url, source="Yahoo Finance", category="NEWS")
            all_items.extend(items)
        return all_items

    def _link_pdf_transcript_to_audio_concalls(
        self,
        db: Session,
        matched_syms: List[str],
        pdf_url: str,
        quarter: Optional[str],
        pub_date: datetime,
    ) -> None:
        """
        Prioritizes official statutory PDF transcripts over Whisper audio transcriptions.
        Links the PDF URL to matching audio-only concall records and invalidates cached
        WHISPER_AUDIO transcripts/analyses so the next analysis uses the clean PDF.
        """
        if not matched_syms or not pdf_url:
            return
        from app.models.market_news import MarketNewsArticle
        window_start = pub_date - timedelta(days=21)
        window_end = pub_date + timedelta(days=21)
        candidates = (
            db.query(MarketNewsArticle)
            .filter(
                MarketNewsArticle.category == "CONCALL",
                MarketNewsArticle.published_at >= window_start,
                MarketNewsArticle.published_at <= window_end,
            )
            .all()
        )
        norm_q = (quarter or "").replace(" ", "").upper()
        for art in candidates:
            art_syms = set(art.symbols or [])
            if not art_syms.intersection(matched_syms):
                continue
            meta = dict(art.metadata_json or {})
            if not meta.get("audio_url"):
                continue
            art_q = (meta.get("quarter") or "").replace(" ", "").upper()
            if norm_q and art_q and norm_q != art_q:
                continue
            if meta.get("transcript_url") == pdf_url:
                continue

            meta["transcript_url"] = pdf_url
            cached_analysis = meta.get("concall_analysis") or {}
            if cached_analysis.get("transcription_source") == "WHISPER_AUDIO":
                meta.pop("concall_analysis", None)
                meta.pop("transcript_text", None)
                logger.info(
                    "Invalidated cached WHISPER_AUDIO analysis for '%s' (%s) in favor of official PDF: %s",
                    art.title,
                    art.id,
                    pdf_url,
                )
            elif meta.get("transcript_text") and not cached_analysis:
                meta.pop("transcript_text", None)

            art.metadata_json = meta
            db.add(art)
            db.commit()

    def sync_all_feeds(self, db: Session, max_targeted_symbols: int = 15) -> Tuple[int, int]:
        """
        Aggregates broad feeds and targeted symbol feeds, saves new articles to database,
        and prunes old entries.
        Returns (articles_fetched, articles_inserted_or_updated).
        """
        active_symbols = self.get_active_portfolio_symbols(db)
        symbol_mappings = self.get_symbol_keyword_mappings(db)
        raw_items: List[Dict[str, Any]] = []

        # Build symbol-to-company-name lookup for targeted Google News searches
        symbol_to_name: Dict[str, str] = {}
        for kw, sym in symbol_mappings.items():
            if sym not in symbol_to_name and len(kw) > len(sym) and kw.lower() not in GENERIC_NAME_BLACKLIST:
                symbol_to_name[sym] = kw

        # 1. Fetch from standard RSS feeds (Macro, Broker Reports, Concalls, Results)
        for cfg in FEED_CONFIGS:
            items = self.fetch_feed_items(cfg["url"], cfg["source"], cfg["category"])
            max_items = cfg.get("max_items")
            if max_items and len(items) > max_items:
                items = items[:max_items]
            raw_items.extend(items)

        # 2. Fetch targeted news, broker research, and Yahoo Finance RSS for up to N active portfolio symbols
        targeted_syms = list(active_symbols)[:max_targeted_symbols]
        targeted_count = 0
        for sym in targeted_syms:
            c_name = symbol_to_name.get(sym)
            raw_items.extend(self.fetch_google_news_for_symbol(sym, company_name=c_name))
            raw_items.extend(self.fetch_broker_research_for_symbol(sym, company_name=c_name))
            targeted_count += 1

        if targeted_syms:
            raw_items.extend(self.fetch_yahoo_finance_rss(targeted_syms))

        logger.info(
            "Fetched %d raw articles (from general feeds + %d targeted symbols)",
            len(raw_items),
            targeted_count,
        )

        inserted_count = 0
        seen_urls: Set[str] = set()
        seen_exchange_items: Dict[str, List[Dict[str, Any]]] = {}

        for item in raw_items:
            url = item["url"]
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            # Generate SHA256 deterministic ID from URL
            article_id = hashlib.sha256(url.encode("utf-8")).hexdigest()
            title = item["title"][:500]
            summary = item["summary"]
            category = item["category"]
            source = item["source"]
            pub_date = item.get("published_at") or datetime.now(timezone.utc)

            # Official stock exchange disclosures (NSE / BSE) are statutory regulatory filings,
            # not editorial or syndicated news articles.
            is_exchange_filing = source in [
                "NSE Announcements",
                "NSE Corporate Actions",
                "BSE Announcements",
                "BSE Corporate Actions",
            ]

            # Match symbols
            full_text = f"{title} {summary}"
            matched_syms = self.match_symbols(full_text, symbol_mappings)

            # Auto-detect concall transcripts and financial results from announcements
            if re.search(
                r"\b(?:transcript|audio\s*recording|earnings\s*(?:call|conference)|concall)\b",
                full_text,
                re.IGNORECASE,
            ):
                category = "CONCALL"
            elif re.search(
                r"\b(?:"
                r"financ(?:ial|e)\s*results?"
                r"|unaudited\s+(?:\w+\s+)?results?"
                r"|audited\s+(?:\w+\s+)?results?"
                r"|quarterly\s*results?"
                r"|half[-\s]*yearly\s*results?"
                r"|annual\s*results?"
                r"|earnings\s*release"
                r"|investor\s*presentation"
                r"|results?\s+for\s+the\s+quarter"
                r"|(?:quarter|half\s*year)\s*ended\s*[-–—:]?\s*\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
                r")\b",
                full_text,
                re.IGNORECASE,
            ):
                category = "RESULT"

            # If exchange description is opaque boilerplate (e.g. "Please find enclosed."),
            # peek at Page 1 of the PDF filing for user-tracked stocks to discover the actual SEBI Subject
            if (
                is_exchange_filing
                and (matched_syms or category in ["CONCALL", "RESULT"])
                and (url.lower().endswith(".pdf") or "corpfiling" in url.lower())
                and _is_generic_exchange_description(summary)
            ):
                peeked = peek_pdf_subject(url, client=self._get_client())
                if peeked:
                    summary = peeked
                    if re.search(r"\b(?:transcript|earnings\s*(?:call|conference)|concall)\b", peeked, re.IGNORECASE):
                        category = "CONCALL"
                        if not re.search(r"\btranscript\b", title, re.IGNORECASE):
                            title = f"{title} - {peeked}"
                    elif re.search(r"\b(?:financial\s*results?|investor\s*presentation)\b", peeked, re.IGNORECASE):
                        category = "RESULT"
                        title = f"{title} - {peeked}"
                    elif re.search(r"\b(?:dividend|bonus|split|sub-division|buyback)\b", peeked, re.IGNORECASE):
                        title = f"{title} - {peeked}"

            # Filter syndicated duplicate headlines across sources (strictly for general editorial NEWS)
            if not is_exchange_filing and category == "NEWS" and headline_deduplicator.is_duplicate(title):
                continue

            # Filter non-financial noise & exam/recruitment/crime spam (exempt official exchange filings)
            if not is_exchange_filing and not relevance_filter.is_financial_relevant(title, summary, category=category):
                continue

            # Extra metadata extraction
            meta: Dict[str, Any] = {}
            if category == "BROKER_REPORT":
                meta.update(extract_broker_metadata(title, summary))
            elif category == "CONCALL":
                meta.update(extract_concall_metadata(title, summary, item.get("enclosure_url"), url=url))
            elif category == "RESULT":
                if (url.lower().endswith(".pdf") or "corpfiling" in url.lower()) and not meta.get("transcript_url"):
                    meta["transcript_url"] = url

            # Corporate action (dividends, splits, bonuses) and governance changes
            corp_meta = extract_corporate_metadata(title, summary, is_exchange_filing=is_exchange_filing)
            if corp_meta:
                meta.update(corp_meta)

            sentiment = calculate_sentiment(full_text)
            if category == "BROKER_REPORT" and "recommendation" in meta:
                rec = meta["recommendation"]
                if rec in ["BUY", "ACCUMULATE"]:
                    sentiment = "POSITIVE"
                elif rec in ["SELL", "REDUCE"]:
                    sentiment = "NEGATIVE"

            # Deduplicate exchange announcements: drop redundant Para A-XBRL stubs when substantive
            # announcement/transcript exists, or update previous XBRL stub with formal filing.
            if is_exchange_filing and matched_syms:
                primary_sym = matched_syms[0]
                norm_sub = extract_core_exchange_subject(title, summary)
                incoming_is_xbrl = is_xbrl_stub(title, summary, url)
                has_att = bool(meta.get("transcript_url") or url.lower().endswith(".pdf"))

                batch_dup_found = False
                for prev in seen_exchange_items.get(primary_sym, []):
                    if are_exchange_subjects_similar(norm_sub, prev["norm_sub"]):
                        if incoming_is_xbrl and not prev["is_xbrl"]:
                            batch_dup_found = True
                            break
                        elif not incoming_is_xbrl and prev["is_xbrl"]:
                            try:
                                old_art = market_news.get(db, prev["id"])
                                if old_art:
                                    db.delete(old_art)
                                    db.commit()
                            except Exception:
                                pass
                            prev["is_xbrl"] = False
                            prev["id"] = article_id
                            break
                        elif has_att and not prev["has_att"]:
                            try:
                                old_art = market_news.get(db, prev["id"])
                                if old_art:
                                    db.delete(old_art)
                                    db.commit()
                            except Exception:
                                pass
                            prev["has_att"] = True
                            prev["id"] = article_id
                            break
                        else:
                            batch_dup_found = True
                            break
                if batch_dup_found:
                    continue

                # Check recent exchange announcements in DB for the same symbol
                since_time = pub_date - timedelta(hours=48)
                recent_exchange_arts = market_news.find_recent_exchange_article(db, symbol=primary_sym, since=since_time)
                db_dup_found = False
                for r_art in recent_exchange_arts:
                    r_norm_sub = extract_core_exchange_subject(r_art.title, r_art.summary or "")
                    if are_exchange_subjects_similar(norm_sub, r_norm_sub):
                        r_is_xbrl = is_xbrl_stub(r_art.title, r_art.summary or "", r_art.url)
                        r_has_att = bool(
                            (r_art.metadata_json or {}).get("transcript_url")
                            or r_art.url.lower().endswith(".pdf")
                        )
                        if incoming_is_xbrl and not r_is_xbrl:
                            db_dup_found = True
                            break
                        elif not incoming_is_xbrl and r_is_xbrl:
                            db.delete(r_art)
                            db.commit()
                            break
                        elif has_att and not r_has_att:
                            db.delete(r_art)
                            db.commit()
                            break
                        else:
                            db_dup_found = True
                            break
                if db_dup_found:
                    continue

                seen_exchange_items.setdefault(primary_sym, []).append({
                    "id": article_id,
                    "norm_sub": norm_sub,
                    "is_xbrl": incoming_is_xbrl,
                    "has_att": has_att,
                })

            obj_in = MarketNewsArticleCreate(
                id=article_id,
                title=title,
                summary=summary,
                url=url,
                source=source,
                category=category,
                published_at=pub_date,
                symbols=matched_syms,
                sentiment=sentiment,
                metadata_json=meta if meta else None,
            )

            try:
                market_news.create_or_update(db, obj_in=obj_in)
                inserted_count += 1
                if category == "CONCALL" and meta and meta.get("transcript_url") and matched_syms:
                    self._link_pdf_transcript_to_audio_concalls(
                        db,
                        matched_syms=matched_syms,
                        pdf_url=meta["transcript_url"],
                        quarter=meta.get("quarter"),
                        pub_date=pub_date,
                    )
            except Exception as e:
                logger.debug("Failed to upsert article %s: %s", article_id, e)

        # Prune articles older than 30 days
        try:
            pruned = market_news.prune_older_than(db, days=30)
            if pruned > 0:
                logger.info("Pruned %d market news articles older than 30 days", pruned)
        except Exception as e:
            logger.warning("Error pruning old news articles: %s", e)

        # Purge existing noise articles and disambiguate tickers
        try:
            del_noise, upd_syms = market_news.purge_noise_and_disambiguate(db, filter_instance=relevance_filter)
            if del_noise > 0 or upd_syms > 0:
                logger.info("Purged %d noise articles and cleaned %d ticker tags", del_noise, upd_syms)
        except Exception as e:
            logger.warning("Error cleaning noise articles: %s", e)

        # Retroactively tag untagged articles within 30 days against active symbols
        if symbol_mappings:
            try:
                retagged = market_news.retroactively_tag_symbols(
                    db,
                    matcher_callback=lambda text: self.match_symbols(text, symbol_mappings),
                    days=30,
                )
                if retagged > 0:
                    logger.info("Retroactively tagged %d articles with active symbols", retagged)
            except Exception as e:
                logger.warning("Error retroactively tagging articles: %s", e)

        return len(raw_items), inserted_count


news_service = MarketNewsService()

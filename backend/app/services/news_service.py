import email.utils
import hashlib
import html
import logging
import re
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
                if len(clean_name) >= 4:
                    mappings[clean_name] = clean_ticker
                stripped = re.sub(
                    r"\s+(Limited|Ltd\.?|Corporation|Corp\.?|India)\b.*",
                    "",
                    clean_name,
                    flags=re.IGNORECASE,
                ).strip()
                if len(stripped) >= 4 and stripped.lower() not in ["stock", "equity", "share", "shares"]:
                    mappings[stripped] = clean_ticker

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

    def fetch_google_news_for_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetches targeted Google News RSS for a specific equity ticker."""
        query = f"{symbol} stock OR share price india"
        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        return self.fetch_feed_items(url, source="Google News", category="NEWS")

    def sync_all_feeds(self, db: Session, max_targeted_symbols: int = 15) -> Tuple[int, int]:
        """
        Aggregates broad feeds and targeted symbol feeds, saves new articles to database,
        and prunes old entries.
        Returns (articles_fetched, articles_inserted_or_updated).
        """
        active_symbols = self.get_active_portfolio_symbols(db)
        symbol_mappings = self.get_symbol_keyword_mappings(db)
        raw_items: List[Dict[str, Any]] = []

        # 1. Fetch from standard RSS feeds (Macro, Broker Reports, Concalls, Results)
        for cfg in FEED_CONFIGS:
            items = self.fetch_feed_items(cfg["url"], cfg["source"], cfg["category"])
            max_items = cfg.get("max_items")
            if max_items and len(items) > max_items:
                items = items[:max_items]
            raw_items.extend(items)

        # 2. Fetch targeted news for up to N active portfolio symbols
        targeted_count = 0
        for sym in list(active_symbols)[:max_targeted_symbols]:
            sym_items = self.fetch_google_news_for_symbol(sym)
            raw_items.extend(sym_items)
            targeted_count += 1

        logger.info(
            "Fetched %d raw articles (from general feeds + %d targeted symbols)",
            len(raw_items),
            targeted_count,
        )

        inserted_count = 0
        seen_urls: Set[str] = set()

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

            # Auto-detect concall transcripts and audio recording disclosures from exchange announcements
            if is_exchange_filing and re.search(
                r"\b(?:transcript|audio\s*recording|earnings\s*(?:call|conference)|concall)\b",
                full_text,
                re.IGNORECASE,
            ):
                category = "CONCALL"

            # If exchange description is opaque boilerplate (e.g. "Please find enclosed."),
            # peek at Page 1 of the PDF filing for user-tracked stocks to discover the actual SEBI Subject
            if (
                is_exchange_filing
                and (matched_syms or category == "CONCALL")
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

            # Filter syndicated duplicate headlines across sources (strictly for general editorial NEWS)

            # Extra metadata extraction
            meta: Dict[str, Any] = {}
            if category == "BROKER_REPORT":
                meta.update(extract_broker_metadata(title, summary))
            elif category == "CONCALL":
                meta.update(extract_concall_metadata(title, summary, item.get("enclosure_url"), url=url))

            sentiment = calculate_sentiment(full_text)
            if category == "BROKER_REPORT" and "recommendation" in meta:
                rec = meta["recommendation"]
                if rec in ["BUY", "ACCUMULATE"]:
                    sentiment = "POSITIVE"
                elif rec in ["SELL", "REDUCE"]:
                    sentiment = "NEGATIVE"

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

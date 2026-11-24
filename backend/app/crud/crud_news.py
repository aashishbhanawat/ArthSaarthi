from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.models.market_news import MarketNewsArticle
from app.schemas.market_news import MarketNewsArticleCreate, MarketNewsArticleOut


class CRUDMarketNews:
    def get(self, db: Session, article_id: str) -> Optional[MarketNewsArticle]:
        return db.query(MarketNewsArticle).filter(MarketNewsArticle.id == article_id).first()

    def get_by_url(self, db: Session, url: str) -> Optional[MarketNewsArticle]:
        return db.query(MarketNewsArticle).filter(MarketNewsArticle.url == url).first()

    def create_or_update(
        self, db: Session, *, obj_in: MarketNewsArticleCreate
    ) -> MarketNewsArticle:
        existing = (
            db.query(MarketNewsArticle)
            .filter(
                sa.or_(
                    MarketNewsArticle.id == obj_in.id,
                    MarketNewsArticle.url == obj_in.url,
                )
            )
            .first()
        )
        if existing:
            existing.title = obj_in.title
            existing.summary = obj_in.summary
            existing.source = obj_in.source
            existing.category = obj_in.category
            existing.published_at = obj_in.published_at
            existing.symbols = list(set(existing.symbols + obj_in.symbols))
            existing.sentiment = obj_in.sentiment
            if obj_in.metadata_json:
                merged_meta = existing.metadata_json or {}
                merged_meta.update(obj_in.metadata_json)
                existing.metadata_json = merged_meta
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        db_obj = MarketNewsArticle(
            id=obj_in.id,
            title=obj_in.title,
            summary=obj_in.summary,
            url=obj_in.url,
            source=obj_in.source,
            category=obj_in.category,
            published_at=obj_in.published_at,
            symbols=obj_in.symbols,
            sentiment=obj_in.sentiment,
            metadata_json=obj_in.metadata_json,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_feed(
        self,
        db: Session,
        *,
        symbols: Optional[List[str]] = None,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        skip: int = 0,
        limit: int = 30,
    ) -> Tuple[List[MarketNewsArticleOut], int]:
        query = db.query(MarketNewsArticle)

        if category and category != "ALL":
            query = query.filter(MarketNewsArticle.category == category)

        if sentiment and sentiment != "ALL":
            query = query.filter(MarketNewsArticle.sentiment == sentiment)

        if symbols:
            # Match articles tagged with any of the requested symbols
            # Works across both SQLite and PostgreSQL via cast to String
            symbol_clauses = [
                sa.cast(MarketNewsArticle.symbols, sa.String).ilike(f'%"{sym}"%')
                for sym in symbols
            ]
            query = query.filter(sa.or_(*symbol_clauses))

        total = query.count()
        articles = (
            query.order_by(MarketNewsArticle.published_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [MarketNewsArticleOut.model_validate(a) for a in articles], total

    def get_summary_counts(
        self,
        db: Session,
        *,
        symbols: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Returns counts per category and the top 5 latest items.
        """
        base_query = db.query(MarketNewsArticle)
        if symbols:
            symbol_clauses = [
                sa.cast(MarketNewsArticle.symbols, sa.String).ilike(f'%"{sym}"%')
                for sym in symbols
            ]
            base_query = base_query.filter(sa.or_(*symbol_clauses))

        news_count = (
            base_query.filter(MarketNewsArticle.category == "NEWS").count()
        )
        broker_count = (
            base_query.filter(MarketNewsArticle.category == "BROKER_REPORT").count()
        )
        concall_count = (
            base_query.filter(MarketNewsArticle.category == "CONCALL").count()
        )
        result_count = (
            base_query.filter(MarketNewsArticle.category == "RESULT").count()
        )

        latest = (
            base_query.order_by(MarketNewsArticle.published_at.desc())
            .limit(5)
            .all()
        )

        return {
            "news_count": news_count,
            "broker_reports_count": broker_count,
            "concalls_count": concall_count,
            "results_count": result_count,
            "latest_items": [MarketNewsArticleOut.model_validate(a) for a in latest],
        }

    def find_recent_exchange_article(
        self, db: Session, *, symbol: str, since: datetime
    ) -> List[MarketNewsArticle]:
        """Finds recent exchange disclosures for the symbol within the time window."""
        return (
            db.query(MarketNewsArticle)
            .filter(
                MarketNewsArticle.published_at >= since,
                MarketNewsArticle.source.in_([
                    "NSE Announcements",
                    "NSE Corporate Actions",
                    "BSE Announcements",
                    "BSE Corporate Actions",
                ]),
                sa.cast(MarketNewsArticle.symbols, sa.String).ilike(f'%"{symbol}"%'),
            )
            .all()
        )

    def prune_older_than(self, db: Session, *, days: int = 30) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        deleted = (
            db.query(MarketNewsArticle)
            .filter(MarketNewsArticle.published_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted

    def retroactively_tag_symbols(
        self,
        db: Session,
        *,
        matcher_callback,
        days: int = 30,
    ) -> int:
        """
        Retroactively scans articles from the last N days that have empty symbols:
        invokes matcher_callback(full_text) to tag newly tracked symbols.
        Returns the count of updated articles.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        untagged = (
            db.query(MarketNewsArticle)
            .filter(
                MarketNewsArticle.published_at >= cutoff,
                sa.or_(
                    sa.cast(MarketNewsArticle.symbols, sa.String).in_(["[]", "null", ""]),
                    MarketNewsArticle.symbols.is_(None),
                ),
            )
            .all()
        )
        updated_count = 0
        for art in untagged:
            full_text = f"{art.title} {art.summary or ''}"
            matched = matcher_callback(full_text)
            if matched:
                art.symbols = matched
                db.add(art)
                updated_count += 1

        if updated_count > 0:
            db.commit()
        return updated_count

    def purge_noise_and_disambiguate(
        self, db: Session, *, filter_instance=None
    ) -> Tuple[int, int]:
        """
        Retroactively scans all market news articles:
        1. Deletes articles that fail financial relevance / match noise filters.
        2. Disambiguates ticker symbols (e.g. removes false SCI tags).
        Returns (deleted_articles_count, updated_articles_count).
        """
        if filter_instance is None:
            from app.ml.relevance_filter import relevance_filter
            filter_instance = relevance_filter

        articles = db.query(MarketNewsArticle).all()
        deleted_count = 0
        updated_count = 0

        for a in articles:
            full_text = f"{a.title} {a.summary or ''}"
            # Check if article is noise or non-financial
            if not filter_instance.is_financial_relevant(a.title, a.summary, a.category):
                db.delete(a)
                deleted_count += 1
                continue

            # Validate attached symbols
            if a.symbols:
                valid_syms = [
                    sym for sym in a.symbols
                    if filter_instance.validate_ticker(sym, a.title, a.summary)
                ]
                if set(valid_syms) != set(a.symbols):
                    a.symbols = valid_syms
                    db.add(a)
                    updated_count += 1
                # If article lost all symbols and was a targeted news feed item, purge it
                if not a.symbols and a.category == "NEWS" and a.source == "Google News":
                    db.delete(a)
                    deleted_count += 1
                    continue

            # Retroactively reclassify RESULT category if not already set (e.g. UNAUDITED FINANCE RESULT)
            if a.category != "RESULT" and re.search(
                r"\b(?:"
                r"financ(?:ial|e)\s*results?"
                r"|unaudited\s+(?:\w+\s+)?results?"
                r"|audited\s+(?:\w+\s+)?results?"
                r"|quarterly\s*results?"
                r"|half[-\s]*yearly\s*results?"
                r"|annual\s*results?"
                r"|investor\s*presentation"
                r"|results?\s+for\s+the\s+quarter"
                r"|(?:quarter|half\s*year)\s*ended\s*[-–—:]?\s*\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
                r")\b",
                full_text,
                re.IGNORECASE,
            ):
                a.category = "RESULT"
                from app.services.news_service import extract_quarter_from_text
                q_inferred = extract_quarter_from_text(full_text)
                meta = dict(a.metadata_json or {})
                if q_inferred and not meta.get("quarter"):
                    meta["quarter"] = q_inferred
                if (a.url.lower().endswith(".pdf") or "corpfiling" in a.url.lower()) and not meta.get("transcript_url"):
                    meta["transcript_url"] = a.url
                a.metadata_json = meta if meta else None
                db.add(a)
                updated_count += 1

            # Clean up spurious dividend tags on editorial screening/yield articles
            if a.metadata_json and a.metadata_json.get("action_type") == "DIVIDEND":
                is_exchange = a.source in [
                    "NSE Announcements",
                    "NSE Corporate Actions",
                    "BSE Announcements",
                    "BSE Corporate Actions",
                ]
                is_editorial_yield = bool(
                    re.search(
                        r"\b(?:dividend\s+yield|dividend\s+income|attractive\s+dividend|dividend\s+stocks?|dividend\s+picks?|stocks?\s+with\s+.*dividend|high\s+dividend\s+yield)\b",
                        full_text,
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
                        r"record\s+date\s+for\s+dividend|ex-dividend\s+date)\b",
                        full_text,
                        re.IGNORECASE,
                    )
                )
                if not is_exchange and is_editorial_yield and not has_div_declaration:
                    cleaned_meta = dict(a.metadata_json)
                    cleaned_meta.pop("action_type", None)
                    cleaned_meta.pop("dividend_amount", None)
                    a.metadata_json = cleaned_meta if cleaned_meta else None
                    db.add(a)
                    updated_count += 1

        # Deduplicate exchange announcements: remove redundant XBRL stubs when substantive filing exists
        exchange_arts = (
            db.query(MarketNewsArticle)
            .filter(
                MarketNewsArticle.source.in_([
                    "NSE Announcements",
                    "NSE Corporate Actions",
                    "BSE Announcements",
                    "BSE Corporate Actions",
                ])
            )
            .order_by(MarketNewsArticle.published_at.desc())
            .all()
        )
        seen_sym_filings: Dict[str, List[MarketNewsArticle]] = {}
        for ea in exchange_arts:
            syms = ea.symbols or []
            is_xbrl = bool(
                re.search(r"\b(?:para\s+[a-z]-xbrl|xbrl)\b", f"{ea.title} {ea.summary or ''}", re.IGNORECASE)
                or ea.url.lower().endswith(".xml")
            )
            sub_raw = re.sub(
                r"(?i)\b(?:has informed the exchange about|disclosure under regulation\s*\d+|para\s*[a-z]-xbrl|xbrl|updates?|intimation|regarding)\b",
                " ",
                f"{ea.title} {ea.summary or ''}",
            )
            ea_words = {w[:5] for w in re.sub(r"[^\w\s]", " ", sub_raw).lower().split() if len(w) >= 3 and w not in {"the", "and", "for", "with"}}

            dropped = False
            for s in syms:
                for prev in seen_sym_filings.get(s, []):
                    # Check subject overlap
                    prev_sub_raw = re.sub(
                        r"(?i)\b(?:has informed the exchange about|disclosure under regulation\s*\d+|para\s*[a-z]-xbrl|xbrl|updates?|intimation|regarding)\b",
                        " ",
                        f"{prev.title} {prev.summary or ''}",
                    )
                    prev_words = {w[:5] for w in re.sub(r"[^\w\s]", " ", prev_sub_raw).lower().split() if len(w) >= 3 and w not in {"the", "and", "for", "with"}}
                    if ea_words and prev_words:
                        overlap = len(ea_words & prev_words)
                        min_len = min(len(ea_words), len(prev_words))
                        if min_len > 0 and (overlap / min_len) >= 0.5:
                            prev_is_xbrl = bool(
                                re.search(r"\b(?:para\s+[a-z]-xbrl|xbrl)\b", f"{prev.title} {prev.summary or ''}", re.IGNORECASE)
                                or prev.url.lower().endswith(".xml")
                            )
                            if is_xbrl and not prev_is_xbrl:
                                db.delete(ea)
                                deleted_count += 1
                                dropped = True
                                break
                            elif not is_xbrl and prev_is_xbrl:
                                db.delete(prev)
                                deleted_count += 1
                            else:
                                # Cross-exchange duplicate (e.g. BSE and NSE duplicate disclosures)
                                ea_has_att = bool((ea.metadata_json or {}).get("transcript_url") or ea.url.lower().endswith(".pdf"))
                                prev_has_att = bool((prev.metadata_json or {}).get("transcript_url") or prev.url.lower().endswith(".pdf"))
                                if ea_has_att and not prev_has_att:
                                    db.delete(prev)
                                    deleted_count += 1
                                else:
                                    db.delete(ea)
                                    deleted_count += 1
                                    dropped = True
                                    break
                if dropped:
                    break
                seen_sym_filings.setdefault(s, []).append(ea)

        db.commit()
        return deleted_count, updated_count


market_news = CRUDMarketNews()

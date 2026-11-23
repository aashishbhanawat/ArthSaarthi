from datetime import datetime, timedelta, timezone
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

    def prune_older_than(self, db: Session, *, days: int = 30) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        deleted = (
            db.query(MarketNewsArticle)
            .filter(MarketNewsArticle.published_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted

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
                    if filter_instance.validate_ticker(sym, full_text)
                ]
                if set(valid_syms) != set(a.symbols):
                    a.symbols = valid_syms
                    db.add(a)
                    updated_count += 1

        db.commit()
        return deleted_count, updated_count


market_news = CRUDMarketNews()

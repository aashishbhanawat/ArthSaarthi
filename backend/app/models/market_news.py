from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class MarketNewsArticle(Base):
    __tablename__ = "market_news_articles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # SHA-256 of url or GUID
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(30), nullable=False, default="NEWS", index=True
    )  # NEWS, BROKER_REPORT, CONCALL, RESULT
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    symbols: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    sentiment: Mapped[str] = mapped_column(
        String(20), nullable=False, default="NEUTRAL"
    )  # POSITIVE, NEGATIVE, NEUTRAL
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_market_news_published_at_desc", published_at.desc()),
        Index("ix_market_news_category_pub", "category", published_at.desc()),
    )

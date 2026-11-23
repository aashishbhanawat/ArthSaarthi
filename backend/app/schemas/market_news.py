from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class MarketNewsArticleBase(BaseModel):
    title: str
    summary: Optional[str] = None
    url: str
    source: str
    category: str = "NEWS"  # NEWS, BROKER_REPORT, CONCALL, RESULT
    published_at: datetime
    symbols: List[str] = []
    sentiment: str = "NEUTRAL"  # POSITIVE, NEGATIVE, NEUTRAL
    metadata_json: Optional[Dict[str, Any]] = None


class MarketNewsArticleCreate(MarketNewsArticleBase):
    id: str


class MarketNewsArticleOut(MarketNewsArticleBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchFeedResponse(BaseModel):
    items: List[MarketNewsArticleOut]
    total: int
    symbols: List[str] = []


class ResearchFeedSummary(BaseModel):
    news_count: int
    broker_reports_count: int
    concalls_count: int
    results_count: int
    latest_items: List[MarketNewsArticleOut] = []


class NewsRefreshResponse(BaseModel):
    message: str
    articles_fetched: int
    articles_inserted: int
    status: str = "success"

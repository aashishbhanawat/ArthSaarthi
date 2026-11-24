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


class ConcallAnalysisRequest(BaseModel):
    transcript_text: Optional[str] = None


class ToneBreakdown(BaseModel):
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    overall: str
    average_tone_score: float = 0.0
    sample_size: int = 0


class GuidanceMetric(BaseModel):
    category: str
    text: str


class RedFlagItem(BaseModel):
    text: str
    score: float


class ConcallAnalysisResponse(BaseModel):
    article_id: str
    title: str
    quarter: Optional[str] = None
    management_tone: ToneBreakdown
    qa_tone: ToneBreakdown
    tone_gap_alert: Optional[float] = None
    tone_divergence_summary: Optional[str] = None
    hedge_rate_per_100w: Optional[float] = None
    topic_sentiment: Optional[Dict[str, float]] = None
    red_flags: List[RedFlagItem] = []
    guidance_metrics: List[GuidanceMetric] = []
    top_takeaways: List[str] = []
    key_themes: List[str] = []
    transcription_source: str = "TRANSCRIPT"

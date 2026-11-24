import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models
from app.core.dependencies import get_current_active_user
from app.crud.crud_news import market_news
from app.db.session import get_db
from app.ml.concall_analyzer import concall_analyzer
from app.ml.whisper_engine import whisper_engine
from app.models.asset import Asset
from app.models.market_news import MarketNewsArticle
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.market_news import (
    ConcallAnalysisRequest,
    ConcallAnalysisResponse,
    NewsRefreshResponse,
    ResearchFeedResponse,
    ResearchFeedSummary,
)
from app.services.news_service import news_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_user_tracked_symbols(db: Session, user_id) -> List[str]:
    """Helper to get unique ticker symbols from the user's holdings and watchlists."""
    symbols = set()

    # 1. From user holdings
    holding_symbols = (
        db.query(Asset.ticker_symbol)
        .join(Transaction, Transaction.asset_id == Asset.id)
        .join(Portfolio, Portfolio.id == Transaction.portfolio_id)
        .filter(Portfolio.user_id == user_id)
        .filter(Asset.asset_type.in_(["STOCK", "ETF", "FOREIGN_STOCK"]))
        .distinct()
        .all()
    )
    for row in holding_symbols:
        if row[0]:
            clean = row[0].split(".")[0].upper().strip()
            if clean:
                symbols.add(clean)

    # 2. From user watchlists
    watchlist_symbols = (
        db.query(Asset.ticker_symbol)
        .join(WatchlistItem, WatchlistItem.asset_id == Asset.id)
        .join(Watchlist, Watchlist.id == WatchlistItem.watchlist_id)
        .filter(Watchlist.user_id == user_id)
        .filter(Asset.asset_type.in_(["STOCK", "ETF", "FOREIGN_STOCK"]))
        .distinct()
        .all()
    )
    for row in watchlist_symbols:
        if row[0]:
            clean = row[0].split(".")[0].upper().strip()
            if clean:
                symbols.add(clean)

    return sorted(list(symbols))


@router.get(
    "/feed",
    response_model=ResearchFeedResponse,
    summary="Get portfolio research and news feed",
)
def get_research_feed(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    category: Optional[str] = Query(None, description="Category filter (NEWS, BROKER_REPORT, CONCALL, RESULT, ALL)"),
    symbol: Optional[str] = Query(None, description="Specific ticker symbol filter e.g. RECLTD"),
    sentiment: Optional[str] = Query(None, description="Sentiment filter (POSITIVE, NEGATIVE, NEUTRAL, ALL)"),
    only_holdings: bool = Query(True, description="Filter strictly to user holdings/watchlists if available"),
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
) -> ResearchFeedResponse:
    """
    Returns research feed items (news, broker reports, concalls, results)
    filtered by user portfolio holdings and watchlists.
    """
    user_symbols = _get_user_tracked_symbols(db, current_user.id)

    filter_symbols: Optional[List[str]] = None
    if symbol and symbol != "ALL":
        filter_symbols = [symbol.upper().strip()]
    elif only_holdings and user_symbols:
        filter_symbols = user_symbols

    items, total = market_news.get_feed(
        db,
        symbols=filter_symbols,
        category=category,
        sentiment=sentiment,
        skip=skip,
        limit=limit,
    )

    return ResearchFeedResponse(
        items=items,
        total=total,
        symbols=user_symbols,
    )


@router.get(
    "/summary",
    response_model=ResearchFeedSummary,
    summary="Get research feed summary counts and highlights",
)
def get_research_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    only_holdings: bool = Query(True),
) -> ResearchFeedSummary:
    """
    Returns counts for News, Broker Reports, Concalls, and Results,
    along with latest highlight cards.
    """
    user_symbols = _get_user_tracked_symbols(db, current_user.id)
    filter_symbols = user_symbols if (only_holdings and user_symbols) else None

    summary_data = market_news.get_summary_counts(db, symbols=filter_symbols)
    return ResearchFeedSummary(**summary_data)


@router.post(
    "/refresh",
    response_model=NewsRefreshResponse,
    summary="Trigger immediate synchronization of market research feeds",
)
def trigger_news_refresh(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> NewsRefreshResponse:
    """
    Manually triggers feed synchronization across all configured sources.
    """
    fetched, saved = news_service.sync_all_feeds(db)
    return NewsRefreshResponse(
        message=f"Feed synchronization complete: {fetched} fetched, {saved} saved/updated.",
        articles_fetched=fetched,
        articles_inserted=saved,
        status="success",
    )


@router.post(
    "/{article_id}/analyze-concall",
    response_model=ConcallAnalysisResponse,
    summary="Analyze earnings concall transcript and audio using edge ML models",
)
def analyze_concall(
    article_id: str,
    payload: Optional[ConcallAnalysisRequest] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> ConcallAnalysisResponse:
    """
    Runs non-LLM extractive concall analysis (FinBERT tone profiling, guidance mining,
    extractive TextRank summarization, topic extraction).
    Falls back to Whisper speech-to-text if audio is available and model is active.
    """
    article = db.query(MarketNewsArticle).filter(MarketNewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    meta = dict(article.metadata_json or {})

    # 1. Check if custom transcript was provided in request
    transcript = payload.transcript_text.strip() if (payload and payload.transcript_text) else None
    source = "USER_INPUT"

    # 2. Check if already analyzed and no override text is provided
    if not transcript and "concall_analysis" in meta:
        return ConcallAnalysisResponse(**meta["concall_analysis"])

    # 3. Check for pre-existing transcript in metadata
    if not transcript:
        if meta.get("transcript_text"):
            transcript = meta["transcript_text"]
            source = "TRANSCRIPT"

    # 4. Check for audio URL and Whisper fallback
    if not transcript and meta.get("audio_url"):
        if whisper_engine.is_available:
            try:
                transcript = whisper_engine.transcribe_audio_file(meta["audio_url"])
                source = "WHISPER_AUDIO"
                meta["transcript_text"] = transcript
            except Exception as e:
                logger.warning("Whisper audio transcription failed: %s. Falling back to summary.", e)
                transcript = f"{article.title}. {article.summary or ''}"
                source = "SUMMARY"
        else:
            logger.info("Whisper model not downloaded. Falling back to title and summary.")
            transcript = f"{article.title}. {article.summary or ''}"
            source = "SUMMARY"

    # 5. Last fallback: analyze title and summary
    if not transcript:
        transcript = f"{article.title}. {article.summary or ''}"
        source = "SUMMARY"

    # Run extractive intelligence pipeline
    analysis = concall_analyzer.analyze(transcript)

    analysis_data = {
        "article_id": article.id,
        "title": article.title,
        "quarter": meta.get("quarter"),
        "management_tone": analysis["management_tone"],
        "qa_tone": analysis["qa_tone"],
        "guidance_metrics": analysis["guidance_metrics"],
        "top_takeaways": analysis["top_takeaways"],
        "key_themes": analysis["key_themes"],
        "transcription_source": source,
    }

    # Cache result in metadata_json
    meta["concall_analysis"] = analysis_data
    article.metadata_json = meta
    db.add(article)
    db.commit()

    return ConcallAnalysisResponse(**analysis_data)


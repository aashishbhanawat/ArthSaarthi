import logging
import threading
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

_concall_lock = threading.Lock()
_in_flight_concalls: set[str] = set()
_recent_concall_cache: dict[str, dict] = {}


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


def _find_matching_pdf_transcript(db: Session, article: MarketNewsArticle) -> Optional[str]:
    """
    Searches MarketNewsArticle for an official BSE/NSE PDF transcript matching this concall
    by symbol overlap or company name tokens within +/- 21 days.
    """
    import re
    from datetime import timedelta

    if not article.published_at:
        return None
    window_start = article.published_at - timedelta(days=21)
    window_end = article.published_at + timedelta(days=21)
    candidates = (
        db.query(MarketNewsArticle)
        .filter(
            MarketNewsArticle.id != article.id,
            MarketNewsArticle.published_at >= window_start,
            MarketNewsArticle.published_at <= window_end,
            MarketNewsArticle.url.ilike("%.pdf%"),
        )
        .all()
    )
    art_syms = set(article.symbols or [])
    stop_words = {
        "results", "earnings", "call", "for", "limited", "ltd", "india", "industries",
    }

    def _extract_company_tokens(text_val: str) -> set[str]:
        return {
            w for w in re.findall(r"[a-z0-9]+", (text_val or "").lower())
            if len(w) > 2
            and w not in stop_words
            and not re.match(r"^(?:fy|cy)?\d{2,4}$", w)
            and not re.match(r"^[qh][1-4]$", w)
        }

    art_tokens = _extract_company_tokens(article.title or "")
    for cand in candidates:
        cand_text = f"{cand.title} {cand.summary or ''} {cand.url}".lower()
        if "transcript" not in cand_text:
            continue
        cand_syms = set(cand.symbols or [])
        if art_syms and cand_syms and art_syms.intersection(cand_syms):
            return (cand.metadata_json or {}).get("transcript_url") or cand.url
        cand_tokens = _extract_company_tokens(cand.title or "")
        if art_tokens and cand_tokens and len(art_tokens.intersection(cand_tokens)) >= 1:
            return (cand.metadata_json or {}).get("transcript_url") or cand.url
    return None


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
        with _concall_lock:
            cached_fallback = _recent_concall_cache.get(article_id)
        if cached_fallback and not (payload and payload.transcript_text):
            return ConcallAnalysisResponse(**cached_fallback)
        logger.warning("Concall analysis requested for non-existent article_id: %s", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    logger.info("Analyzing concall for article '%s' (%s)", article.title, article.id)

    meta = dict(article.metadata_json or {})

    # 1. Check if custom transcript was provided in request
    transcript = payload.transcript_text.strip() if (payload and payload.transcript_text) else None
    source = "USER_INPUT"

    # 2. Discover official PDF transcript if not yet linked, and prioritize PDF over WHISPER_AUDIO
    if not transcript and not meta.get("transcript_url") and not (payload and payload.check_only):
        discovered_pdf = _find_matching_pdf_transcript(db, article)
        if discovered_pdf:
            meta["transcript_url"] = discovered_pdf
            logger.info("Linked discovered PDF transcript for '%s': %s", article.title, discovered_pdf)

    if (
        not transcript
        and meta.get("transcript_url")
        and (meta.get("concall_analysis") or {}).get("transcription_source") == "WHISPER_AUDIO"
    ):
        logger.info(
            "Invalidating cached WHISPER_AUDIO analysis for '%s' (%s) in favor of PDF transcript",
            article.title,
            article.id,
        )
        meta.pop("concall_analysis", None)
        meta.pop("transcript_text", None)

    # 2a. Check if already analyzed and no override text is provided
    if not transcript and "concall_analysis" in meta:
        return ConcallAnalysisResponse(**meta["concall_analysis"])

    # 2b. Polling status check: never trigger new transcription/analysis
    if payload and payload.check_only:
        with _concall_lock:
            if article_id in _in_flight_concalls:
                raise HTTPException(status_code=409, detail="Concall analysis is still in progress.")
        raise HTTPException(status_code=404, detail="Concall analysis has not been generated yet.")

    # 2c. Deduplicate concurrent requests for the same article
    if not transcript:
        with _concall_lock:
            if article_id in _in_flight_concalls:
                raise HTTPException(
                    status_code=409,
                    detail="Concall transcription and analysis is already in progress in the background.",
                )
            _in_flight_concalls.add(article_id)

    article_title = article.title
    article_summary = article.summary
    # Release Postgres connection back to QueuePool before long-running network/CPU work
    if db.bind and db.bind.dialect.name != "sqlite":
        db.expunge(article)
        db.close()

    try:
        # 3. Check for pre-existing transcript in metadata or fetch from transcript_url (e.g. BSE PDF filing)
        if not transcript:
            if meta.get("transcript_text"):
                transcript = meta["transcript_text"]
                source = "TRANSCRIPT"
            elif meta.get("transcript_url"):
                t_url = meta["transcript_url"]
                try:
                    import io

                    import httpx
                    import pdfplumber
                    pdf_headers = {
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                        ),
                        "Accept": "application/pdf,*/*",
                    }
                    with httpx.Client(headers=pdf_headers, timeout=30.0, follow_redirects=True) as client:
                        resp = client.get(t_url)
                        if resp.status_code == 200:
                            with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                                pages_text = [p.extract_text() or "" for p in pdf.pages]
                                full_pdf_text = "\n".join(pages_text).strip()
                                if full_pdf_text:
                                    transcript = full_pdf_text
                                    source = "BSE_PDF" if "bseindia" in t_url.lower() else "TRANSCRIPT_PDF"
                                    meta["transcript_text"] = transcript
                except Exception as e:
                    logger.warning("Failed to download or parse PDF transcript from %s: %s", t_url, e)

        # 4. Check for audio URL and Whisper fallback
        if not transcript and meta.get("audio_url"):
            if whisper_engine.is_available:
                try:
                    transcript = whisper_engine.transcribe_audio_file(meta["audio_url"])
                    source = "WHISPER_AUDIO"
                    meta["transcript_text"] = transcript
                except Exception as e:
                    logger.warning("Whisper audio transcription failed: %s", e)
                    raise HTTPException(
                        status_code=400,
                        detail=f"Audio transcription failed: {str(e)}. Please paste the official conference call transcript text.",
                    )
            else:
                logger.warning(
                    "Concall analysis rejected for article '%s' (%s): only audio podcast is available and speech-to-text runtime is disabled.",
                    article_title,
                    article_id,
                )
                raise HTTPException(
                    status_code=400,
                    detail="Only audio podcast is available for this concall. Please paste the conference call transcript text in the 'Paste Transcript' tab or read the statutory BSE/NSE filing PDF.",
                )

        # 5. Last fallback: analyze title and summary
        if not transcript:
            transcript = f"{article_title}. {article_summary or ''}"
            source = "SUMMARY"

        # Run extractive intelligence pipeline
        analysis = concall_analyzer.analyze(transcript)

        analysis_data = {
            "article_id": article_id,
            "title": article_title,
            "quarter": meta.get("quarter"),
            "management_tone": analysis["management_tone"],
            "qa_tone": analysis["qa_tone"],
            "tone_gap_alert": analysis.get("tone_gap_alert"),
            "tone_divergence_summary": analysis.get("tone_divergence_summary"),
            "hedge_rate_per_100w": analysis.get("hedge_rate_per_100w"),
            "topic_sentiment": analysis.get("topic_sentiment"),
            "red_flags": analysis.get("red_flags", []),
            "guidance_metrics": analysis["guidance_metrics"],
            "top_takeaways": analysis["top_takeaways"],
            "key_themes": analysis["key_themes"],
            "transcription_source": source,
        }

        # Cache result in metadata_json using a fresh short-lived DB checkout
        target_article = db.query(MarketNewsArticle).filter(MarketNewsArticle.id == article_id).first()
        if target_article:
            meta["concall_analysis"] = analysis_data
            target_article.metadata_json = meta
            db.add(target_article)
            db.commit()
        else:
            # Article was pruned (e.g. >30d expiry) during transcription; retain briefly in memory for polling
            with _concall_lock:
                if len(_recent_concall_cache) >= 50:
                    _recent_concall_cache.pop(next(iter(_recent_concall_cache)))
                _recent_concall_cache[article_id] = analysis_data

        return ConcallAnalysisResponse(**analysis_data)
    finally:
        with _concall_lock:
            _in_flight_concalls.discard(article_id)


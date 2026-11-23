from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models
from app.core.dependencies import get_current_active_user
from app.crud.crud_news import market_news
from app.db.session import get_db
from app.models.asset import Asset
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.market_news import (
    NewsRefreshResponse,
    ResearchFeedResponse,
    ResearchFeedSummary,
)
from app.services.news_service import news_service

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

import logging
import time
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.cache.utils import cache_analytics_data
from app.models.user import User
from app.services.financial_data_service import financial_data_service

logger = logging.getLogger(__name__)


def _calculate_dashboard_summary(db: Session, *, user: User) -> Dict[str, Any]:
    """
    Calculates the dashboard summary metrics for a given user by aggregating
    summaries from all their portfolios.
    """
    start_time = time.time()
    from app import crud  # Local import to break circular dependency

    portfolios = crud.portfolio.get_multi_by_owner(db=db, user_id=user.id)
    if not portfolios:
        return {
            "total_value": Decimal("0.0"),
            "total_unrealized_pnl": Decimal("0.0"),
            "total_realized_pnl": Decimal("0.0"),
            "top_movers": [],
            "asset_allocation": [],
        }

    # Initialize aggregate values
    agg_total_value = Decimal("0.0")
    agg_total_unrealized_pnl = Decimal("0.0")
    agg_total_realized_pnl = Decimal("0.0")
    agg_holdings = []

    # Aggregate data from all portfolios
    for portfolio in portfolios:
        portfolio_data = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio.id
        )
        summary = portfolio_data.summary

        agg_total_value += summary.total_value
        agg_total_unrealized_pnl += summary.total_unrealized_pnl
        agg_total_realized_pnl += summary.total_realized_pnl

        agg_holdings.extend(portfolio_data.holdings)

    # Calculate top movers from aggregated holdings
    top_movers = []
    for h in agg_holdings:
        # Only include assets with a non-zero day's P&L and a valid quantity
        if h.days_pnl is not None and h.days_pnl != 0 and h.quantity > 0:
            # This is already in INR after the holding.py fix
            daily_change_per_unit = h.days_pnl / h.quantity

            # The holding schema now contains the asset's currency.
            # We need to pass this to the frontend so it can display the correct
            # currency symbol for the `current_price`.
            asset_currency = "INR" # Default
            asset = crud.asset.get(db, id=h.asset_id)
            if asset:
                asset_currency = asset.currency

            top_movers.append(
                {
                    "ticker_symbol": h.ticker_symbol,
                    "currency": asset_currency,
                    "name": h.asset_name,
                    "current_price": h.current_price,
                    "daily_change": daily_change_per_unit,
                    "daily_change_percentage": h.days_pnl_percentage,
                }
            )
    top_movers.sort(key=lambda x: abs(x["daily_change_percentage"]), reverse=True)

    # Calculate asset allocation from aggregated holdings
    asset_allocation_map = defaultdict(Decimal)
    for h in agg_holdings:
        asset_allocation_map[h.ticker_symbol] += h.current_value

    formatted_allocation = [
        {"ticker": ticker, "value": value}
        for ticker, value in asset_allocation_map.items()
    ]

    end_time = time.time()
    logger.info(
        "Dashboard summary for user %s took %.4f seconds.",
        user.id,
        end_time - start_time,
    )
    return {
        "total_value": agg_total_value,
        "total_unrealized_pnl": agg_total_unrealized_pnl,
        "total_realized_pnl": agg_total_realized_pnl,
        "top_movers": top_movers[:5],
        "asset_allocation": formatted_allocation,
    }


def _get_portfolio_history(
    db: Session, *, user: User, range_str: str
) -> List[Dict[str, Any]]:
    """
    Calculates the portfolio's total value over a specified time range.
    """
    from app import crud  # Local import to break circular dependency

    end_date = date.today()
    if range_str == "7d":
        start_date = end_date - timedelta(days=7)
    elif range_str == "30d":
        start_date = end_date - timedelta(days=30)
    elif range_str == "1y":
        start_date = end_date - timedelta(days=365)
    else:  # "all"
        first_transaction = (
            db.query(crud.transaction.model)
            .filter(crud.transaction.model.user_id == user.id)
            .order_by(crud.transaction.model.transaction_date.asc())
            .first()
        )
        start_date = (
            first_transaction.transaction_date.date() if first_transaction else end_date
        )

    all_user_assets = (
        db.query(crud.asset.model)
        .join(crud.transaction.model)
        .filter(crud.transaction.model.user_id == user.id)
        .distinct()
        .all()
    )
    if not all_user_assets:
        return []

    # Filter for assets that are likely to have market data from yfinance
    yfinance_supported_types = ["STOCK", "ETF", "MUTUAL_FUND"]
    market_traded_assets = [asset for asset in all_user_assets
                            if asset.asset_type in yfinance_supported_types]

    asset_details_list = [
        {
            "ticker_symbol": asset.ticker_symbol,
            "exchange": asset.exchange,
            "asset_type": asset.asset_type,
        }
        for asset in market_traded_assets
    ]

    historical_prices = financial_data_service.get_historical_prices(
        assets=asset_details_list, start_date=start_date, end_date=end_date
    )

    transactions = (
        db.query(crud.transaction.model)
        .filter(
            crud.transaction.model.user_id == user.id,
            crud.transaction.model.transaction_date <= end_date,
        )
        .order_by(crud.transaction.model.transaction_date.asc())
        .all()
    )

    history_points = []
    current_day = start_date
    transaction_idx = 0
    daily_holdings = defaultdict(Decimal)
    last_known_prices = {}

    # Calculate initial holdings up to the start_date
    initial_transactions = [
        t for t in transactions if t.transaction_date.date() < start_date
    ]
    for t in initial_transactions:
        ticker = t.asset.ticker_symbol
        if t.transaction_type.lower() == "buy":
            daily_holdings[ticker] += t.quantity
        else:
            daily_holdings[ticker] -= t.quantity

    # Pre-fill last known prices for the day before the window starts
    day_before_start = start_date - timedelta(days=1)
    for ticker in daily_holdings:
        if ticker in historical_prices:
            # Find the most recent price on or before the day before the window
            relevant_dates = [
                d for d in historical_prices[ticker] if d <= day_before_start
            ]
            if relevant_dates:
                last_known_prices[ticker] = historical_prices[ticker][
                    max(relevant_dates)
                ]
    transaction_idx = len(initial_transactions)

    while current_day <= end_date:
        while (
            transaction_idx < len(transactions)
            and transactions[transaction_idx].transaction_date.date() == current_day
        ):
            t = transactions[transaction_idx]
            ticker = t.asset.ticker_symbol
            if t.transaction_type.lower() == "buy":
                daily_holdings[ticker] += t.quantity
            else:
                daily_holdings[ticker] -= t.quantity
            transaction_idx += 1

        day_total_value = Decimal("0.0")
        for ticker, quantity in daily_holdings.items():
            if quantity > 0:
                if (
                    ticker in historical_prices
                    and current_day in historical_prices[ticker]
                ):
                    last_known_prices[ticker] = historical_prices[ticker][current_day]

                if ticker in last_known_prices:
                    day_total_value += quantity * last_known_prices[ticker]
        history_points.append({"date": current_day, "value": day_total_value})
        current_day += timedelta(days=1)

    return history_points


class CRUDDashboard:
    @cache_analytics_data(prefix="analytics:dashboard_summary", arg_names=["user_id"])
    def get_summary(self, db: Session, *, user_id: uuid.UUID) -> Dict[str, Any]:
        user = db.get(User, user_id)
        if not user:
            # This case should ideally not be hit if called from a valid session
            return {}
        return _calculate_dashboard_summary(db=db, user=user)

    @cache_analytics_data(
        prefix="analytics:dashboard_history", arg_names=["user", "range_str"]
    )
    def get_history(
        self, db: Session, *, user: User, range_str: str
    ) -> List[Dict[str, Any]]:
        return _get_portfolio_history(db=db, user=user, range_str=range_str)

    def get_allocation(
        self, db: Session, *, user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        # Note: This will not be cached independently. It will be fast if get_summary
        # has been called recently, as the underlying calculation will be cached.
        summary_data = self.get_summary(db=db, user_id=user_id)
        return summary_data.get("asset_allocation", [])


dashboard = CRUDDashboard()

import logging
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
from typing import Any, Dict, List
import uuid
import numpy as np
from sqlalchemy.orm import Session
from pyxirr import xirr

from app import crud
from app.schemas.analytics import AnalyticsResponse
from app.services.financial_data_service import financial_data_service

logger = logging.getLogger(__name__)


def _get_portfolio_current_value(db: Session, portfolio_id: uuid.UUID) -> Decimal:
    """Calculates the current market value of a single portfolio."""
    transactions = crud.transaction.get_multi_by_portfolio(db=db, portfolio_id=portfolio_id)
    if not transactions:
        return Decimal("0.0")

    live_holdings = defaultdict(lambda: {"quantity": Decimal("0.0"), "exchange": None})
    for t in transactions:
        ticker = t.asset.ticker_symbol
        live_holdings[ticker]["exchange"] = t.asset.exchange
        if t.transaction_type.lower() == 'buy':
            live_holdings[ticker]["quantity"] += t.quantity
        elif t.transaction_type.lower() == 'sell':
            live_holdings[ticker]["quantity"] -= t.quantity

    assets_to_price = [
        {"ticker_symbol": ticker, "exchange": data["exchange"]}
        for ticker, data in live_holdings.items() if data["quantity"] > 0
    ]
    
    if not assets_to_price:
        return Decimal("0.0")

    current_prices_details = financial_data_service.get_current_prices(assets_to_price)
    
    total_value = Decimal("0.0")
    for ticker, data in live_holdings.items():
        if data["quantity"] > 0 and ticker in current_prices_details:
            price_info = current_prices_details[ticker]
            current_price = price_info["current_price"]
            total_value += data["quantity"] * current_price
            
    return total_value


def _get_single_portfolio_history(db: Session, portfolio_id: uuid.UUID, time_range: str) -> List[Dict[str, Any]]:
    """Calculates the total value of a single portfolio over a specified time range."""
    end_date = date.today()
    
    transactions = crud.transaction.get_multi_by_portfolio(db=db, portfolio_id=portfolio_id)
    if not transactions:
        return []

    first_transaction_date = min(t.transaction_date.date() for t in transactions)

    if time_range == "7d":
        start_date = end_date - timedelta(days=7)
    elif time_range == "30d":
        start_date = end_date - timedelta(days=30)
    elif time_range == "1y":
        start_date = end_date - timedelta(days=365)
    else:  # "all"
        start_date = first_transaction_date

    # Ensure start_date is not before the first transaction
    start_date = max(start_date, first_transaction_date)

    portfolio_assets = db.query(crud.asset.model).join(crud.transaction.model).filter(crud.transaction.model.portfolio_id == portfolio_id).distinct().all()
    if not portfolio_assets:
        return []

    asset_details_list = [
        {"ticker_symbol": asset.ticker_symbol, "exchange": asset.exchange}
        for asset in portfolio_assets
    ]

    historical_prices = financial_data_service.get_historical_prices(
        assets=asset_details_list, start_date=start_date, end_date=end_date
    )

    history_points = []
    current_day = start_date
    daily_holdings = defaultdict(Decimal)
    last_known_prices = {}

    # Calculate initial holdings up to the start_date
    initial_transactions = [t for t in transactions if t.transaction_date.date() < start_date]
    for t in initial_transactions:
        ticker = t.asset.ticker_symbol
        if t.transaction_type.lower() == 'buy':
            daily_holdings[ticker] += t.quantity
        else:
            daily_holdings[ticker] -= t.quantity

    # Pre-fill last known prices for the day before the window starts
    day_before_start = start_date - timedelta(days=1)
    for ticker in daily_holdings:
        if ticker in historical_prices:
            relevant_dates = [d for d in historical_prices[ticker] if d <= day_before_start]
            if relevant_dates:
                last_known_prices[ticker] = historical_prices[ticker][max(relevant_dates)]
    
    # Filter transactions to only those within the date window for daily processing
    window_transactions = sorted([t for t in transactions if t.transaction_date.date() >= start_date], key=lambda t: t.transaction_date)
    transaction_idx = 0

    while current_day <= end_date:
        while transaction_idx < len(window_transactions) and window_transactions[transaction_idx].transaction_date.date() == current_day:
            t = window_transactions[transaction_idx]
            ticker = t.asset.ticker_symbol
            if t.transaction_type.lower() == 'buy':
                daily_holdings[ticker] += t.quantity
            else:
                daily_holdings[ticker] -= t.quantity
            transaction_idx += 1

        day_total_value = Decimal("0.0")
        for ticker, quantity in daily_holdings.items():
            if quantity > 0:
                if ticker in historical_prices and current_day in historical_prices[ticker]:
                    last_known_prices[ticker] = historical_prices[ticker][current_day]
                
                if ticker in last_known_prices:
                    day_total_value += quantity * last_known_prices[ticker]
        history_points.append({"date": current_day.isoformat(), "value": float(day_total_value)})
        current_day += timedelta(days=1)

    return history_points


def _calculate_xirr(db: Session, portfolio_id: uuid.UUID) -> float:
    """
    Calculates the Extended Internal Rate of Return (XIRR) for a portfolio.
    """
    transactions = crud.transaction.get_multi_by_portfolio(
        db=db, portfolio_id=portfolio_id
    )
    if not transactions:
        return 0.0

    # 1. Construct cash flows from transactions
    dates = []
    values = []
    for tx in transactions:
        dates.append(tx.transaction_date)
        # Buys are cash outflows (-), sells are cash inflows (+)
        amount = tx.quantity * tx.price_per_unit
        if tx.transaction_type == "BUY":
            values.append(float(-amount))
        else:
            values.append(float(amount))

    # 2. Add the current market value as the final cash inflow
    current_value = _get_portfolio_current_value(db=db, portfolio_id=portfolio_id)

    dates.append(date.today())
    values.append(float(current_value))

    # 3. Calculate XIRR
    if not any(v > 0 for v in values) or not any(v < 0 for v in values):
        return 0.0

    try:
        # Add a small initial guess to help convergence
        result = xirr(dates, values, guess=0.1)
        return result if result is not None else 0.0
    except Exception as e:
        logger.error(f"Could not calculate XIRR for portfolio {portfolio_id}: {e}")
        return 0.0


def _calculate_sharpe_ratio(db: Session, portfolio_id: uuid.UUID) -> float:
    """Calculates the Sharpe Ratio for a portfolio."""
    history_points = _get_single_portfolio_history(
        db=db, portfolio_id=portfolio_id, time_range="all"
    )
    if len(history_points) < 2:
        return 0.0

    daily_values = [p['value'] for p in history_points]
    # Ensure no zero values before division
    daily_values = [v if v > 0 else 1e-9 for v in daily_values]
    
    daily_returns = np.diff(daily_values) / daily_values[:-1]

    if len(daily_returns) == 0 or np.std(daily_returns) == 0:
        return 0.0

    # Assuming risk-free rate is 0
    sharpe_ratio = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252)
    return sharpe_ratio


def get_portfolio_analytics(db: Session, portfolio_id: uuid.UUID) -> AnalyticsResponse:
    """
    Calculates advanced analytics for a given portfolio.
    """
    xirr_value = _calculate_xirr(db=db, portfolio_id=portfolio_id)
    sharpe_ratio_value = _calculate_sharpe_ratio(db=db, portfolio_id=portfolio_id)

    return AnalyticsResponse(
        xirr=round(xirr_value, 4),
        sharpe_ratio=round(sharpe_ratio_value, 4),
    )

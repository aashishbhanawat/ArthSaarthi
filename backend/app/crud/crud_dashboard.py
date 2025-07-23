from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from app import crud
from app.models.user import User
from app.services.financial_data_service import financial_data_service


def _calculate_dashboard_summary(db: Session, *, user: User) -> Dict[str, Any]:
    """
    Calculates the dashboard summary metrics for a given user.
    """
    portfolios = crud.portfolio.get_multi_by_owner(db=db, user_id=user.id)
    if not portfolios:
        return {
            "total_value": Decimal("0.0"),
            "total_unrealized_pnl": Decimal("0.0"),
            "total_realized_pnl": Decimal("0.0"),
            "top_movers": [],
            "asset_allocation": [],
        }

    holdings = defaultdict(Decimal)
    for portfolio in portfolios:
        for transaction in portfolio.transactions:
            if transaction.transaction_type.lower() == "buy":
                holdings[transaction.asset.ticker_symbol] += transaction.quantity
            else:
                holdings[transaction.asset.ticker_symbol] -= transaction.quantity

    asset_allocation = []
    total_value = Decimal("0.0")
    for ticker, quantity in holdings.items():
        if quantity > 0:
            try:
                current_price = financial_data_service.get_asset_price(ticker)
                value = quantity * current_price
                total_value += value
                asset_allocation.append({"ticker": ticker, "value": value})
            except Exception:
                # If price lookup fails, we can't calculate its value, so we skip it.
                pass

    return {
        "total_value": total_value,
        "total_unrealized_pnl": Decimal("0.0"),  # Placeholder
        "total_realized_pnl": Decimal("0.0"),  # Placeholder
        "top_movers": [],  # Placeholder
        "asset_allocation": asset_allocation,
    }


def _get_portfolio_history(db: Session, *, user: User, range_str: str) -> List[Dict[str, Any]]:
    """
    Calculates the portfolio's total value over a specified time range.
    """
    end_date = date.today()
    if range_str == "7d":
        start_date = end_date - timedelta(days=7)
    elif range_str == "30d":
        start_date = end_date - timedelta(days=30)
    elif range_str == "1y":
        start_date = end_date - timedelta(days=365)
    else:  # "all"
        first_transaction = db.query(crud.transaction.model).filter(crud.transaction.model.user_id == user.id).order_by(crud.transaction.model.transaction_date.asc()).first()
        start_date = first_transaction.transaction_date.date() if first_transaction else end_date

    transactions = db.query(crud.transaction.model).filter(
        crud.transaction.model.user_id == user.id,
        crud.transaction.model.transaction_date <= end_date
    ).order_by(crud.transaction.model.transaction_date.asc()).all()

    history_points = []
    current_day = start_date
    transaction_idx = 0
    daily_holdings = defaultdict(Decimal)

    # Calculate initial holdings up to the start_date
    initial_transactions = [t for t in transactions if t.transaction_date.date() < start_date]
    for t in initial_transactions:
        if t.transaction_type.lower() == 'buy':
            daily_holdings[t.asset.ticker_symbol] += t.quantity
        else:
            daily_holdings[t.asset.ticker_symbol] -= t.quantity
    transaction_idx = len(initial_transactions)

    while current_day <= end_date:
        while transaction_idx < len(transactions) and transactions[transaction_idx].transaction_date.date() == current_day:
            t = transactions[transaction_idx]
            if t.transaction_type.lower() == 'buy':
                daily_holdings[t.asset.ticker_symbol] += t.quantity
            else:
                daily_holdings[t.asset.ticker_symbol] -= t.quantity
            transaction_idx += 1

        day_total_value = Decimal("0.0")
        for ticker, quantity in daily_holdings.items():
            if quantity > 0:
                try:
                    day_total_value += quantity * financial_data_service.get_asset_price(ticker)
                except Exception:
                    pass  # Skip assets for which price is not available
        history_points.append({"date": current_day, "value": day_total_value})
        current_day += timedelta(days=1)

    return history_points


class CRUDDashboard:
    def get_summary(self, db: Session, *, user: User) -> Dict[str, Any]:
        return _calculate_dashboard_summary(db=db, user=user)

    def get_history(self, db: Session, *, user: User, range_str: str) -> List[Dict[str, Any]]:
        return _get_portfolio_history(db=db, user=user, range_str=range_str)

    def get_allocation(self, db: Session, *, user: User) -> List[Dict[str, Any]]:
        summary_data = _calculate_dashboard_summary(db=db, user=user)
        return summary_data.get("asset_allocation", [])


dashboard = CRUDDashboard()
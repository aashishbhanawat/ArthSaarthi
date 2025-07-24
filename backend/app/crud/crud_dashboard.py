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

    holdings = defaultdict(lambda: {"quantity": Decimal("0.0"), "exchange": "N/A"})
    for portfolio in portfolios:
        for transaction in portfolio.transactions:
            asset = transaction.asset
            if transaction.transaction_type.lower() == 'buy':
                holdings[asset.ticker_symbol]["quantity"] += transaction.quantity
            else:
                holdings[asset.ticker_symbol]["quantity"] -= transaction.quantity
            holdings[asset.ticker_symbol]["exchange"] = asset.exchange

    assets_to_price = [
        {"ticker_symbol": ticker, "exchange": data["exchange"]}
        for ticker, data in holdings.items() if data["quantity"] > 0
    ]

    current_prices = financial_data_service.get_current_prices(assets_to_price) if assets_to_price else {}

    asset_allocation = []
    total_value = Decimal("0.0")
    for ticker, data in holdings.items():
        if data["quantity"] > 0 and ticker in current_prices:
            value = data["quantity"] * current_prices[ticker]
            total_value += value
            asset_allocation.append({"ticker": ticker, "value": value})

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

    all_user_assets = db.query(crud.asset.model).join(crud.transaction.model).filter(crud.transaction.model.user_id == user.id).distinct().all()
    if not all_user_assets:
        return []

    asset_details_list = [
        {"ticker_symbol": asset.ticker_symbol, "exchange": asset.exchange}
        for asset in all_user_assets
    ]

    historical_prices = financial_data_service.get_historical_prices(
        assets=asset_details_list, start_date=start_date, end_date=end_date
    )

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
        ticker = t.asset.ticker_symbol
        if t.transaction_type.lower() == 'buy':
            daily_holdings[ticker] += t.quantity
        else:
            daily_holdings[ticker] -= t.quantity
    transaction_idx = len(initial_transactions)

    while current_day <= end_date:
        while transaction_idx < len(transactions) and transactions[transaction_idx].transaction_date.date() == current_day:
            t = transactions[transaction_idx]
            ticker = t.asset.ticker_symbol
            if t.transaction_type.lower() == 'buy':
                daily_holdings[ticker] += t.quantity
            else:
                daily_holdings[ticker] -= t.quantity
            transaction_idx += 1

        day_total_value = Decimal("0.0")
        for ticker, quantity in daily_holdings.items():
            if quantity > 0 and ticker in historical_prices and current_day in historical_prices[ticker]:
                day_total_value += quantity * historical_prices[ticker][current_day]
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
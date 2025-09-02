from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.financial_data_service import financial_data_service


def _calculate_dashboard_summary(db: Session, *, user: User) -> Dict[str, Any]:
    """
    Calculates the dashboard summary metrics for a given user, including P/L.
    """
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

    # 1. Get all transactions across all portfolios and sort them by date
    all_transactions = []
    for portfolio in portfolios:
        all_transactions.extend(portfolio.transactions)
    all_transactions.sort(key=lambda t: t.transaction_date)

    # 2. Calculate cost basis and realized P/L by iterating through transactions
    live_holdings = defaultdict(
        lambda: {
            "quantity": Decimal("0.0"),
            "total_cost": Decimal("0.0"),
            "name": "N/A",
            "exchange": "N/A",
            "asset_type": "N/A",
        }
    )
    total_realized_pnl = Decimal("0.0")

    for t in all_transactions:
        ticker = t.asset.ticker_symbol
        live_holdings[ticker]["name"] = t.asset.name
        live_holdings[ticker]["exchange"] = t.asset.exchange
        live_holdings[ticker]["asset_type"] = t.asset.asset_type

        if t.transaction_type.lower() == "buy":
            live_holdings[ticker]["quantity"] += t.quantity
            live_holdings[ticker]["total_cost"] += t.quantity * t.price_per_unit
        elif t.transaction_type.lower() == "sell":
            if live_holdings[ticker]["quantity"] > 0:
                average_cost = (
                    live_holdings[ticker]["total_cost"]
                    / live_holdings[ticker]["quantity"]
                )
                realized_pnl_for_sale = (t.price_per_unit - average_cost) * t.quantity
                total_realized_pnl += realized_pnl_for_sale
                live_holdings[ticker]["total_cost"] -= t.quantity * average_cost
                live_holdings[ticker]["quantity"] -= t.quantity

    # 3. Get current prices for all currently held assets
    assets_to_price = [
        {
            "ticker_symbol": ticker,
            "exchange": data["exchange"],
            "asset_type": data["asset_type"],
        }
        for ticker, data in live_holdings.items()
        if data["quantity"] > 0
    ]
    current_prices_details = (
        financial_data_service.get_current_prices(assets_to_price)
        if assets_to_price
        else {}
    )

    # 4. Calculate final summary metrics (Total Value, Unrealized P/L, etc.)
    total_value = Decimal("0.0")
    total_unrealized_pnl = Decimal("0.0")
    asset_allocation = []
    top_movers = []

    for ticker, data in live_holdings.items():
        if data["quantity"] > 0 and ticker in current_prices_details:
            price_info = current_prices_details[ticker]
            current_price = price_info["current_price"]
            previous_close = price_info["previous_close"]

            value = data["quantity"] * current_price
            total_value += value
            asset_allocation.append({"ticker": ticker, "value": value})

            if data["quantity"] > 0:  # Avoid division by zero for sold-off assets
                average_cost = data["total_cost"] / data["quantity"]
                total_unrealized_pnl += (current_price - average_cost) * data[
                    "quantity"
                ]

            daily_change = current_price - previous_close
            daily_change_percentage = (
                (daily_change / previous_close) * 100 if previous_close else 0
            )
            top_movers.append(
                {
                    "ticker_symbol": ticker,
                    "name": data["name"],
                    "current_price": current_price,
                    "daily_change": daily_change,
                    "daily_change_percentage": daily_change_percentage,
                }
            )

    top_movers.sort(key=lambda x: abs(x["daily_change_percentage"]), reverse=True)

    return {
        "total_value": total_value,
        "total_unrealized_pnl": total_unrealized_pnl,
        "total_realized_pnl": total_realized_pnl,
        "top_movers": top_movers[:5],
        "asset_allocation": asset_allocation,
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

    asset_details_list = [
        {
            "ticker_symbol": asset.ticker_symbol,
            "exchange": asset.exchange,
            "asset_type": asset.asset_type,
        }
        for asset in all_user_assets
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
    def get_summary(self, db: Session, *, user: User) -> Dict[str, Any]:
        return _calculate_dashboard_summary(db=db, user=user)

    def get_history(
        self, db: Session, *, user: User, range_str: str
    ) -> List[Dict[str, Any]]:
        return _get_portfolio_history(db=db, user=user, range_str=range_str)

    def get_allocation(self, db: Session, *, user: User) -> List[Dict[str, Any]]:
        summary_data = _calculate_dashboard_summary(db=db, user=user)
        return summary_data.get("asset_allocation", [])


dashboard = CRUDDashboard()

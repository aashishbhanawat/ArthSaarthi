import logging
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Tuple

import numpy as np
from dateutil.relativedelta import relativedelta
from pyxirr import xirr
from sqlalchemy.orm import Session

from app import crud, schemas
from app.crud.crud_holding import _calculate_fd_current_value
from app.schemas.analytics import AnalyticsResponse, AssetAnalytics
from app.services.financial_data_service import financial_data_service

logger = logging.getLogger(__name__)


def _get_portfolio_current_value(db: Session, portfolio_id: uuid.UUID) -> Decimal:
    """Calculates the current market value of a single portfolio."""
    transactions = crud.transaction.get_multi_by_portfolio(
        db=db, portfolio_id=portfolio_id
    )
    if not transactions:
        return Decimal("0.0")

    live_holdings = defaultdict(
        lambda: {"quantity": Decimal("0.0"), "exchange": None, "asset_type": None}
    )
    for t in transactions:
        ticker = t.asset.ticker_symbol
        live_holdings[ticker]["exchange"] = t.asset.exchange
        live_holdings[ticker]["asset_type"] = t.asset.asset_type
        if t.transaction_type.lower() == "buy":
            live_holdings[ticker]["quantity"] += t.quantity
        elif t.transaction_type.lower() == "sell":
            live_holdings[ticker]["quantity"] -= t.quantity

    assets_to_price = [
        {
            "ticker_symbol": ticker,
            "exchange": data["exchange"],
            "asset_type": data["asset_type"],
        } for ticker, data in live_holdings.items() if data["quantity"] > 0
    ]

    if not assets_to_price:
        return Decimal("0.0")

    current_prices_details = financial_data_service.get_current_prices(assets_to_price)

    total_value = Decimal("0.0")
    for ticker, data in live_holdings.items():
        if data["quantity"] > 0 and ticker in current_prices_details:
            price_info = current_prices_details[ticker]
            current_price = Decimal(str(price_info["current_price"]))
            total_value += data["quantity"] * current_price

    return total_value


def _get_single_portfolio_history(
    db: Session, portfolio_id: uuid.UUID, time_range: str
) -> List[Dict[str, Any]]:
    """Calculates the total value of a single portfolio over a specified time range."""
    end_date = date.today()

    transactions = crud.transaction.get_multi_by_portfolio(
        db=db, portfolio_id=portfolio_id
    )
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

    portfolio_assets = (
        db.query(crud.asset.model)
        .join(crud.transaction.model)
        .filter(crud.transaction.model.portfolio_id == portfolio_id)
        .distinct()
        .all()
    )
    if not portfolio_assets:
        return []

    asset_details_list = [
        {
            "ticker_symbol": asset.ticker_symbol,
            "exchange": asset.exchange,
            "asset_type": asset.asset_type,
        }
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
            relevant_dates = [
                d for d in historical_prices[ticker] if d <= day_before_start
            ]
            if relevant_dates:
                last_known_prices[ticker] = historical_prices[ticker][
                    max(relevant_dates)
                ]

    # Filter transactions to only those within the date window for daily processing
    window_transactions = sorted(
        [t for t in transactions if t.transaction_date.date() >= start_date],
        key=lambda t: t.transaction_date,
    )
    transaction_idx = 0

    while current_day <= end_date:
        while (
            transaction_idx < len(window_transactions)
            and window_transactions[transaction_idx].transaction_date.date()
            == current_day
        ):
            t = window_transactions[transaction_idx]
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
        history_points.append(
            {"date": current_day.isoformat(), "value": float(day_total_value)}
        )
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
        dates.append(tx.transaction_date.date())
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
        if result is None or np.isnan(result) or np.isinf(result):
            return 0.0
        return result
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

    daily_values = [p["value"] for p in history_points]
    # Ensure no zero values before division
    daily_values = [v if v > 0 else 1e-9 for v in daily_values]

    daily_returns = np.diff(daily_values) / daily_values[:-1]

    if len(daily_returns) == 0 or np.std(daily_returns) == 0:
        return 0.0

    # Assuming risk-free rate is 0
    sharpe_ratio = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252)

    # Handle non-JSON compliant results like NaN or Infinity.
    if np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio):
        return 0.0
    return sharpe_ratio


def _get_realized_and_unrealized_cash_flows(
    transactions: List[schemas.Transaction],
) -> Tuple[List, List]:
    """
    Applies FIFO logic to separate transactions into realized and unrealized lots.

    Returns a tuple of two lists: (realized_cash_flows, unrealized_cash_flows).
    """
    sorted_txs = sorted(transactions, key=lambda t: t.transaction_date.date())

    # Create copies to avoid mutation and to track remaining quantities.
    buys = [t.model_copy(deep=True) for t in sorted_txs if t.transaction_type == "BUY"]
    sells = [t for t in sorted_txs if t.transaction_type == "SELL"]

    realized_cash_flows = []

    for sell_tx in sells:
        sell_quantity_to_match = sell_tx.quantity

        for buy_tx in buys:
            if sell_quantity_to_match == 0:
                break

            if buy_tx.quantity > 0:
                match_quantity = min(sell_quantity_to_match, buy_tx.quantity)

                # Handle zero-price transactions (e.g., bonus shares) gracefully
                buy_price = (
                    buy_tx.price_per_unit
                    if buy_tx.price_per_unit is not None
                    else Decimal("0.0")
                )
                sell_price = (
                    sell_tx.price_per_unit
                    if sell_tx.price_per_unit is not None
                    else Decimal("0.0")
                )

                buy_cost_for_match = match_quantity * buy_price
                sell_proceeds_for_match = match_quantity * sell_price

                # A closed lot is a pair of cashflows
                realized_cash_flows.append(
                    (buy_tx.transaction_date.date(), float(-buy_cost_for_match))
                )
                realized_cash_flows.append(
                    (sell_tx.transaction_date.date(), float(sell_proceeds_for_match))
                )

                buy_tx.quantity -= match_quantity
                sell_quantity_to_match -= match_quantity

    # The remaining quantities in `buys` are the open lots
    unrealized_cash_flows = []
    for buy_tx in buys:
        if buy_tx.quantity > 0:
            buy_price = (
                buy_tx.price_per_unit
                if buy_tx.price_per_unit is not None
                else Decimal("0.0")
            )
            unrealized_cash_flows.append(
                (buy_tx.transaction_date.date(), float(-buy_tx.quantity * buy_price))
            )

    return realized_cash_flows, unrealized_cash_flows


def _calculate_xirr_from_cashflows(cash_flows: List[Tuple[date, float]]) -> float:
    """A generic XIRR calculation helper."""
    if not cash_flows:
        return 0.0

    dates, values = zip(*cash_flows)

    # XIRR requires at least one positive and one negative cash flow
    if not any(v > 0 for v in values) or not any(v < 0 for v in values):
        return 0.0

    try:
        result = xirr(dates, values, guess=0.1)
        return 0.0 if result is None or np.isnan(result) or np.isinf(result) else result
    except Exception:
        # This can happen if pyxirr fails to converge
        return 0.0


def _get_asset_current_value(
    db: Session, portfolio_id: uuid.UUID, asset_id: uuid.UUID
) -> Decimal:
    """Calculates the current market value of a single asset holding in a portfolio."""
    transactions = crud.transaction.get_multi_by_portfolio_and_asset(
        db=db, portfolio_id=portfolio_id, asset_id=asset_id
    )
    if not transactions:
        return Decimal("0.0")

    asset = crud.asset.get(db=db, id=asset_id)
    if not asset:
        # This case should ideally not be reached if transactions exist for the asset_id
        return Decimal("0.0")

    net_quantity = Decimal("0.0")
    for t in transactions:
        if t.transaction_type.lower() == "buy":
            net_quantity += t.quantity
        elif t.transaction_type.lower() == "sell":
            net_quantity -= t.quantity

    if net_quantity <= 0:
        return Decimal("0.0")

    asset_to_price = [
        {
            "ticker_symbol": asset.ticker_symbol,
            "exchange": asset.exchange,
            "asset_type": asset.asset_type,
        }
    ]
    current_prices_details = financial_data_service.get_current_prices(asset_to_price)

    if asset.ticker_symbol not in current_prices_details:
        return Decimal("0.0")

    price_info = current_prices_details[asset.ticker_symbol]
    current_price = Decimal(str(price_info["current_price"]))

    return net_quantity * current_price


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


def get_fixed_deposit_analytics(
    db: Session, fd_id: uuid.UUID
) -> schemas.FixedDepositAnalytics:
    """
    Calculates advanced analytics for a single Fixed Deposit.
    """
    fd = crud.fixed_deposit.get(db=db, id=fd_id)
    if not fd:
        return schemas.FixedDepositAnalytics(realized_xirr=0.0, unrealized_xirr=0.0)

    principal_outflow = (fd.start_date, -float(fd.principal_amount))
    unrealized_xirr = 0.0
    realized_xirr = 0.0

    if fd.interest_payout == "Cumulative":
        # Cumulative FD logic for Unrealized XIRR
        current_value = _calculate_fd_current_value(
            principal=fd.principal_amount,
            interest_rate=fd.interest_rate,
            start_date=fd.start_date,
            end_date=date.today(),
            compounding_frequency=fd.compounding_frequency,
            interest_payout=fd.interest_payout,
        )
        current_inflow = (date.today(), float(current_value))
        unrealized_xirr = _calculate_xirr_from_cashflows(
            [principal_outflow, current_inflow]
        )

        # Cumulative FD logic for Realized XIRR (if matured)
        if date.today() >= fd.maturity_date:
            maturity_value = _calculate_fd_current_value(
                principal=fd.principal_amount,
                interest_rate=fd.interest_rate,
                start_date=fd.start_date,
                end_date=fd.maturity_date,
                compounding_frequency=fd.compounding_frequency,
                interest_payout=fd.interest_payout,
            )
            maturity_inflow = (fd.maturity_date, float(maturity_value))
            realized_xirr = _calculate_xirr_from_cashflows(
                [principal_outflow, maturity_inflow]
            )
    else:
        # Payout FD logic
        payout_frequency_map = {
            "Monthly": 12,
            "Quarterly": 4,
            "Semi-Annually": 2,
            "Annually": 1,
        }
        payouts_per_year = payout_frequency_map.get(fd.interest_payout)

        if payouts_per_year:
            interest_per_payout = fd.principal_amount * (
                fd.interest_rate
                / Decimal("100.0")
                / Decimal(payouts_per_year)
            )

            # Payout FD logic for Unrealized XIRR
            unrealized_cash_flows = [principal_outflow]
            if payouts_per_year > 0:
                months_interval = 12 // payouts_per_year
                next_payout_date = fd.start_date + relativedelta(
                    months=months_interval
                )
                while next_payout_date <= date.today():
                    unrealized_cash_flows.append(
                        (next_payout_date, float(interest_per_payout))
                    )
                    next_payout_date += relativedelta(months=months_interval)
            unrealized_cash_flows.append(
                (date.today(), float(fd.principal_amount))
            )
            unrealized_xirr = _calculate_xirr_from_cashflows(
                unrealized_cash_flows
            )

            # Payout FD logic for Realized XIRR (if matured)
            if date.today() >= fd.maturity_date:
                realized_cash_flows = [principal_outflow]
                if payouts_per_year > 0:
                    months_interval = 12 // payouts_per_year
                    next_payout_date = fd.start_date + relativedelta(
                        months=months_interval
                    )
                    while next_payout_date <= fd.maturity_date:
                        realized_cash_flows.append(
                            (next_payout_date, float(interest_per_payout))
                        )
                        next_payout_date += relativedelta(
                            months=months_interval
                        )
                realized_cash_flows.append(
                    (fd.maturity_date, float(fd.principal_amount))
                )
                realized_xirr = _calculate_xirr_from_cashflows(
                    realized_cash_flows
                )

    return schemas.FixedDepositAnalytics(
        unrealized_xirr=round(unrealized_xirr, 4),
        realized_xirr=round(realized_xirr, 4),
    )


def get_asset_analytics(
    db: Session, portfolio_id: uuid.UUID, asset_id: uuid.UUID
) -> AssetAnalytics:
    """
    Calculates advanced analytics for a given asset in a portfolio.
    """
    transactions_db = crud.transaction.get_multi_by_portfolio_and_asset(
        db=db, portfolio_id=portfolio_id, asset_id=asset_id
    )
    if not transactions_db:
        return AssetAnalytics(realized_xirr=0.0, unrealized_xirr=0.0)

    # Convert SQLAlchemy models to Pydantic schemas for calculation helpers.
    transactions_schemas = [
        schemas.Transaction.model_validate(tx) for tx in transactions_db
    ]

    realized_cash_flows, unrealized_cash_flows = (
        _get_realized_and_unrealized_cash_flows(transactions_schemas)
    )

    # Calculate realized XIRR from closed lots
    realized_xirr_value = _calculate_xirr_from_cashflows(realized_cash_flows)

    # Calculate unrealized XIRR from open lots + their current market value
    current_value_of_open_lots = _get_asset_current_value(
        db=db, portfolio_id=portfolio_id, asset_id=asset_id
    )
    unrealized_cash_flows.append((date.today(), float(current_value_of_open_lots)))
    unrealized_xirr_value = _calculate_xirr_from_cashflows(unrealized_cash_flows)

    return AssetAnalytics(
        realized_xirr=round(realized_xirr_value, 4),
        unrealized_xirr=round(unrealized_xirr_value, 4),
    )

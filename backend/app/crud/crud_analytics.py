import logging
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Tuple

import numpy as np
from dateutil.relativedelta import relativedelta
from pyxirr import xirr
from sqlalchemy.orm import Session

from app import crud, schemas
from app.crud.crud_dashboard import _get_portfolio_history
from app.crud.crud_holding import (
    _calculate_fd_current_value,
    _calculate_rd_value_at_date,
)
from app.models.fixed_deposit import FixedDeposit
from app.models.recurring_deposit import RecurringDeposit

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _calculate_xirr(dates: List[date], values: List[Decimal]) -> float:
    """Helper function to safely calculate XIRR and return as a rate."""
    if len(dates) < 2 or len(values) < 2:
        return 0.0

    # XIRR requires at least one positive and one negative value
    has_positive = any(v > 0 for v in values)
    has_negative = any(v < 0 for v in values)
    if not (has_positive and has_negative):
        return 0.0

    # pyxirr expects floats
    values_float = [float(v) for v in values]

    try:
        # The pyxirr library returns the rate, e.g., 0.08 for 8%
        result = xirr(dates, values_float)
        # Handle invalid results from the library (e.g., None, NaN)
        if result is None or result != result:
            return 0.0
        return result
    except Exception as e:
        logger.warning(f"XIRR calculation failed: {e}")
        return 0.0


def _get_realized_and_unrealized_cash_flows(
    transactions: List[schemas.Transaction],
) -> Tuple[List[Tuple[date, float]], List[Tuple[date, float]]]:
    """
    Applies FIFO logic to separate transactions into realized and unrealized lots.

    Returns a tuple of two lists: (realized_cash_flows, unrealized_cash_flows).
    """
    sorted_txs = sorted(transactions, key=lambda t: t.transaction_date.date())

    # Create copies to avoid mutation and to track remaining quantities.
    buys = [t.model_copy(deep=True) for t in sorted_txs if t.transaction_type == "BUY"]
    sells = [t for t in sorted_txs if t.transaction_type == "SELL"]
    other_cash_flows = [
        t
        for t in sorted_txs
        if t.transaction_type
        in ("COUPON", "INTEREST_CREDIT", "DIVIDEND", "CONTRIBUTION")
    ]

    realized_cash_flows = []

    for sell_tx in sells:
        sell_quantity_to_match = sell_tx.quantity

        for buy_tx in buys:
            if sell_quantity_to_match == 0:
                break

            if buy_tx.quantity > 0:
                match_quantity = min(sell_quantity_to_match, buy_tx.quantity)

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

                realized_cash_flows.append(
                    (buy_tx.transaction_date.date(), float(-buy_cost_for_match))
                )
                realized_cash_flows.append(
                    (sell_tx.transaction_date.date(), float(sell_proceeds_for_match))
                )

                buy_tx.quantity -= match_quantity
                sell_quantity_to_match -= match_quantity

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

    # Add other positive cash flows (coupons, dividends, etc.) to unrealized flows
    for cf_tx in other_cash_flows:
        # Contributions are outflows, others are inflows
        if cf_tx.transaction_type == "CONTRIBUTION":
            amount = float(-cf_tx.quantity)
        else:
            amount = float(cf_tx.quantity * cf_tx.price_per_unit)
        unrealized_cash_flows.append((cf_tx.transaction_date.date(), amount))

    return realized_cash_flows, unrealized_cash_flows


def _calculate_xirr_from_cashflows_tuple(
    cash_flows: List[Tuple[date, float]],
) -> float:
    """A generic XIRR calculation helper for tuple-based cashflows."""
    if not cash_flows:
        return 0.0
    dates, values = zip(*cash_flows)
    return _calculate_xirr(list(dates), [Decimal(str(v)) for v in values])


class CRUDAnalytics:
    def get_asset_analytics(
        self, db: Session, *, portfolio_id: uuid.UUID, asset_id: uuid.UUID
    ) -> schemas.AssetAnalytics:
        """Calculates analytics for a single asset in a portfolio."""
        asset = crud.asset.get(db, id=asset_id)
        if not asset:
            logger.warning(f"Asset with ID {asset_id} not found.")
            return schemas.AssetAnalytics(realized_xirr=0.0, unrealized_xirr=0.0)
        logger.debug(
            f"Calculating analytics for asset {asset_id} ({asset.ticker_symbol})"
        )

        # We need the current value of the holding, which is calculated in crud_holding
        all_holdings_data = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio_id
        )
        holding = next(
            (h for h in all_holdings_data["holdings"] if h.asset_id == asset_id), None
        )
        if not holding:
            logger.debug(f"No active holding found for asset {asset_id}.")
            return schemas.AssetAnalytics(realized_xirr=0.0, unrealized_xirr=0.0)

        transactions = crud.transaction.get_multi_by_portfolio_and_asset(
            db, portfolio_id=portfolio_id, asset_id=asset_id
        )

        dates = []
        values = []
        realized_xirr = 0.0

        if asset.asset_type == "PPF":
            # For PPF, cash flows are contributions (outflows)
            contributions = [
                tx for tx in transactions if tx.transaction_type == "CONTRIBUTION"
            ]
            if not contributions:
                return schemas.AssetAnalytics(realized_xirr=0.0, unrealized_xirr=0.0)

            for tx in contributions:
                dates.append(tx.transaction_date.date())
                values.append(-tx.quantity)  # Outflow
        else:
            transactions_schemas = [
                schemas.Transaction.model_validate(tx) for tx in transactions
            ]
            (
                realized_cash_flows,
                unrealized_cash_flows,
            ) = _get_realized_and_unrealized_cash_flows(transactions_schemas)

            logger.debug(
                f"Realized cash flows for asset {asset_id}: {realized_cash_flows}"
            )
            realized_xirr = _calculate_xirr_from_cashflows_tuple(realized_cash_flows)

            # For unrealized XIRR, use the unrealized cash flows
            if unrealized_cash_flows:
                dates_tuple, values_float = zip(*unrealized_cash_flows)
                dates = list(dates_tuple)
                values = [Decimal(str(v)) for v in values_float]

        # The current value of the holding is the final inflow for the calculation
        if holding.current_value > 0:
            dates.append(date.today())
            values.append(holding.current_value)

        logger.debug(f"Asset ID: {asset_id}")
        logger.debug(f"Transaction Types: "
                     f"{[tx.transaction_type for tx in transactions]}")
        logger.debug(f"Cashflow Dates: {dates}")
        logger.debug(f"Cashflow Values: {values}")

        logger.debug(f"Unrealized cashflow dates: {dates}")
        logger.debug(f"Unrealized cashflow values: {values}")
        unrealized_xirr = _calculate_xirr(dates, values)

        return schemas.AssetAnalytics(
            realized_xirr=realized_xirr,
            unrealized_xirr=unrealized_xirr,
        )

    def get_fixed_deposit_analytics(
        self, db: Session, *, fd: FixedDeposit
    ) -> schemas.FixedDepositAnalytics:
        """Calculates XIRR for a single Fixed Deposit."""
        logger.debug(f"Calculating analytics for FD {fd.id}")
        dates = []
        values = []

        # Initial investment is an outflow
        dates.append(fd.start_date)
        values.append(-fd.principal_amount)

        today = date.today()

        # Handle periodic interest payouts for non-cumulative FDs
        if fd.interest_payout != "Cumulative":
            payout_frequency_map = {
                "MONTHLY": 1,
                "QUARTERLY": 3,
                "HALF_YEARLY": 6,
                "SEMI-ANNUALLY": 6,
                "ANNUALLY": 12,
            }
            months_interval = payout_frequency_map.get(fd.compounding_frequency.upper())
            if months_interval:
                payouts_per_year = Decimal("12.0") / Decimal(str(months_interval))
                payout_rate = fd.interest_rate / Decimal("100.0") / payouts_per_year
                interest_per_payout = fd.principal_amount * payout_rate

                payout_date = fd.start_date + relativedelta(months=months_interval)
                while payout_date <= today and payout_date <= fd.maturity_date:
                    dates.append(payout_date)
                    values.append(interest_per_payout)
                    payout_date += relativedelta(months=months_interval)

        # Final value is an inflow
        if today >= fd.maturity_date:
            # If matured, the inflow is the maturity value
            maturity_value = _calculate_fd_current_value(
                principal=fd.principal_amount,
                interest_rate=fd.interest_rate,
                start_date=fd.start_date,
                end_date=fd.maturity_date,
                compounding_frequency=fd.compounding_frequency,
                interest_payout=fd.interest_payout,
            )
            dates.append(fd.maturity_date)
            values.append(maturity_value)
            unrealized_xirr = 0.0
            realized_xirr = _calculate_xirr(dates, values)
        else:
            # If active, the inflow is the current value
            # If active, the inflow is the current value
            current_value = _calculate_fd_current_value(
                principal=fd.principal_amount,
                interest_rate=fd.interest_rate,
                start_date=fd.start_date,
                end_date=today,
                compounding_frequency=fd.compounding_frequency,
                interest_payout=fd.interest_payout,
            )
            dates.append(today)
            values.append(current_value)
            unrealized_xirr = _calculate_xirr(dates, values)
            realized_xirr = 0.0

        logger.debug(f"FD cashflow dates: {dates}")
        logger.debug(f"FD cashflow values: {values}")
        logger.debug(f"FD unrealized/realized XIRR: {unrealized_xirr}/{realized_xirr}")
        return schemas.FixedDepositAnalytics(
            realized_xirr=realized_xirr,
            unrealized_xirr=unrealized_xirr,
        )

    def get_recurring_deposit_analytics(
        self, db: Session, *, rd: RecurringDeposit
    ) -> schemas.RecurringDepositAnalytics:
        """Calculates XIRR for a single Recurring Deposit."""
        logger.debug(f"Calculating analytics for RD {rd.id}")
        if not rd:
            return schemas.RecurringDepositAnalytics(unrealized_xirr=0.0)

        dates = []
        values = []
        today = date.today()
        maturity_date = rd.start_date + relativedelta(months=rd.tenure_months)

        # Installments are outflows
        for i in range(rd.tenure_months):
            installment_date = rd.start_date + relativedelta(months=i)
            if installment_date > today:
                break
            dates.append(installment_date)
            values.append(-rd.monthly_installment)

        # Final value is an inflow
        if today >= maturity_date:
            # If matured, the inflow is the maturity value
            final_value = _calculate_rd_value_at_date(
                monthly_installment=rd.monthly_installment,
                interest_rate=rd.interest_rate,
                start_date=rd.start_date,
                tenure_months=rd.tenure_months,
                calculation_date=maturity_date,
            )
            dates.append(maturity_date)
            values.append(final_value)
        else:
            # If active, the inflow is the current value
            final_value = _calculate_rd_value_at_date(
                monthly_installment=rd.monthly_installment,
                interest_rate=rd.interest_rate,
                start_date=rd.start_date,
                tenure_months=rd.tenure_months,
                calculation_date=today,
            )
            dates.append(today)
            values.append(final_value)

        logger.debug(f"RD cashflow dates: {dates}")
        logger.debug(f"RD cashflow values: {values}")
        xirr_value = _calculate_xirr(dates, values)
        logger.debug(f"Calculated RD XIRR: {xirr_value}")
        return schemas.RecurringDepositAnalytics(unrealized_xirr=xirr_value)

    def get_portfolio_analytics(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> schemas.PortfolioAnalytics:
        """Calculates analytics for a whole portfolio."""
        # First, call the holdings summary to ensure any missing PPF interest
        # transactions are created for the current session. This is the key
        # to making the subsequent cash flow calculation correct.
        holdings_data = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio_id
        )

        # Now, gather all transactions and assets to build the cash flow list.
        transactions = crud.transaction.get_multi_by_portfolio(
            db, portfolio_id=portfolio_id
        )
        all_fixed_deposits = crud.fixed_deposit.get_multi_by_portfolio(
            db, portfolio_id=portfolio_id
        )
        all_recurring_deposits = crud.recurring_deposit.get_multi_by_portfolio(
            db, portfolio_id=portfolio_id
        )

        dates = []
        values = []

        # Cashflows from Stocks, MFs, PPF
        for tx in transactions:
            if tx.transaction_type == "BUY":
                dates.append(tx.transaction_date.date())
                values.append(-(tx.quantity * tx.price_per_unit))
            elif tx.transaction_type == "SELL":
                dates.append(tx.transaction_date.date())
                values.append(tx.quantity * tx.price_per_unit)
            elif tx.transaction_type == "CONTRIBUTION":  # For PPF
                dates.append(tx.transaction_date.date())
                values.append(-tx.quantity)
            elif tx.transaction_type == "DIVIDEND":
                dates.append(tx.transaction_date.date())
                values.append(tx.quantity * tx.price_per_unit)

        # Cashflows from Fixed Deposits
        for fd in all_fixed_deposits:
            dates.append(fd.start_date)
            values.append(-fd.principal_amount)

        # Cashflows from Recurring Deposits
        for rd in all_recurring_deposits:
            for i in range(rd.tenure_months):
                installment_date = rd.start_date + relativedelta(months=i)
                if installment_date > date.today():
                    break
                dates.append(installment_date)
                values.append(-rd.monthly_installment)

        # Add current portfolio value as the final cashflow
        # Per FR6.2, the final value for XIRR must be the market value of assets,
        # not the total_value which includes cash from income (which is already
        # accounted for as a separate cash flow).
        current_market_value = sum(h.current_value for h in holdings_data["holdings"])
        if current_market_value > 0:
            dates.append(date.today())
            values.append(current_market_value)

        sharpe_ratio_value = self._calculate_sharpe_ratio(db, portfolio_id)
        xirr_value = _calculate_xirr(dates, values)

        return schemas.PortfolioAnalytics(
            xirr=xirr_value, sharpe_ratio=sharpe_ratio_value
        )

    def _calculate_sharpe_ratio(self, db: Session, portfolio_id: uuid.UUID) -> float:
        """Calculates the Sharpe Ratio for a portfolio."""
        portfolio = crud.portfolio.get(db, id=portfolio_id)
        if not portfolio:
            return 0.0
        user = portfolio.user

        history_points = _get_portfolio_history(db=db, user=user, range_str="all")
        if len(history_points) < 2:
            logger.debug("Sharpe ratio: Not enough history points (<2).")
            return 0.0

        daily_values = [float(p["value"]) for p in history_points]
        daily_values = [v if v > 0 else 1e-9 for v in daily_values]

        daily_returns = np.diff(daily_values) / daily_values[:-1]

        if len(daily_returns) == 0 or np.std(daily_returns) == 0:
            logger.debug("Sharpe ratio: Not enough returns or zero standard deviation.")
            return 0.0

        sharpe_ratio = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252)
        logger.debug(f"Sharpe ratio: Calculated value is {sharpe_ratio}")
        return float(sharpe_ratio) if np.isfinite(sharpe_ratio) else 0.0


def _get_portfolio_current_value(db: Session, portfolio_id: uuid.UUID) -> Decimal:
    """Helper to get the total current value of a portfolio."""
    summary = crud.holding.get_portfolio_holdings_and_summary(
        db, portfolio_id=portfolio_id
    )["summary"]
    return summary.total_value


def _get_asset_current_value(
    db: Session, portfolio_id: uuid.UUID, asset_id: uuid.UUID
) -> Decimal:
    """Helper to get the current value of a single asset in a portfolio."""
    holdings = crud.holding.get_portfolio_holdings_and_summary(
        db, portfolio_id=portfolio_id
    )["holdings"]
    for h in holdings:
        if h.asset_id == asset_id:
            return h.current_value
    return Decimal("0.0")


analytics = CRUDAnalytics()

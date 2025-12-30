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
from app.cache.utils import cache_analytics_data
from app.core.financial_definitions import TRANSACTION_BEHAVIORS, CashFlowType
from app.crud.crud_dashboard import _get_portfolio_history
from app.crud.crud_holding import (
    _calculate_fd_current_value,
    _calculate_rd_value_at_date,
)
from app.models.fixed_deposit import FixedDeposit
from app.models.recurring_deposit import RecurringDeposit
from app.models.transaction import Transaction

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

    # Calculate total cost reduction from DEMERGER events for this asset
    # This scales down the original BUY amounts for correct XIRR
    total_cost_reduction = Decimal("0.0")
    original_cost = Decimal("0.0")
    for t in sorted_txs:
        if t.transaction_type in ("BUY", "ESPP_PURCHASE", "RSU_VEST"):
            price = t.price_per_unit if t.price_per_unit else Decimal("0")
            original_cost += t.quantity * price
        if t.transaction_type == "DEMERGER":
            if t.details and "total_cost_allocated" in t.details:
                total_cost_reduction += Decimal(str(t.details["total_cost_allocated"]))

    # Calculate remaining cost ratio after all demergers
    if original_cost > 0 and total_cost_reduction > 0:
        remaining_ratio = (original_cost - total_cost_reduction) / original_cost
    else:
        remaining_ratio = Decimal("1.0")

    # Create copies to avoid mutation and to track remaining quantities.
    # Scale price_per_unit by remaining_ratio for demerged assets
    buys = []
    for t in sorted_txs:
        if t.transaction_type in ("BUY", "ESPP_PURCHASE", "RSU_VEST"):
            buy_copy = t.model_copy(deep=True)
            if remaining_ratio < Decimal("1.0") and buy_copy.price_per_unit:
                buy_copy.price_per_unit = buy_copy.price_per_unit * remaining_ratio
            buys.append(buy_copy)

    sells = [t for t in sorted_txs if t.transaction_type == "SELL"]
    # Separate income from contributions, as they are handled differently.
    income_flows = [
        t
        for t in sorted_txs
        if t.transaction_type in ("DIVIDEND", "COUPON", "INTEREST_CREDIT")
    ]
    contribution_flows = [
        t for t in sorted_txs if t.transaction_type == "CONTRIBUTION"
    ]

    realized_cash_flows = []

    for sell_tx in sells:
        sell_quantity_to_match = sell_tx.quantity

        for buy_tx in buys:
            if sell_quantity_to_match == 0:
                break

            if buy_tx.quantity > 0:
                match_quantity = min(sell_quantity_to_match, buy_tx.quantity)

                if (
                    buy_tx.transaction_type == "RSU_VEST"
                    and buy_tx.details
                    and "fmv" in buy_tx.details
                ):
                    buy_price = Decimal(str(buy_tx.details["fmv"]))
                else:
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

                # --- FX Rate Adjustment ---
                buy_fx_rate = (
                    Decimal(str(buy_tx.details.get("fx_rate", 1)))
                    if buy_tx.details
                    else Decimal(1)
                )
                sell_fx_rate = (
                    Decimal(str(sell_tx.details.get("fx_rate", 1)))
                    if sell_tx.details
                    else Decimal(1)
                )

                buy_cost_for_match = match_quantity * buy_price * buy_fx_rate
                sell_proceeds_for_match = match_quantity * sell_price * sell_fx_rate

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
            if (
                buy_tx.transaction_type == "RSU_VEST"
                and buy_tx.details
                and "fmv" in buy_tx.details
            ):
                buy_price = Decimal(str(buy_tx.details["fmv"]))
            else:
                buy_price = (
                    buy_tx.price_per_unit
                    if buy_tx.price_per_unit is not None
                    else Decimal("0.0")
                )

            # --- FX Rate Adjustment ---
            buy_fx_rate = (
                Decimal(str(buy_tx.details.get("fx_rate", 1)))
                if buy_tx.details
                else Decimal(1)
            )

            unrealized_cash_flows.append(
                (
                    buy_tx.transaction_date.date(),
                    float(-buy_tx.quantity * buy_price * buy_fx_rate)
                )
            )

    # Prorate each income event based on the holding status AT THAT TIME.
    for income_tx in income_flows:
        # Find total shares bought up to the date of this income event.
        acquisition_types = ("BUY", "ESPP_PURCHASE", "RSU_VEST")
        bought_at_income_date = sum(
            t.quantity
            for t in sorted_txs
            if t.transaction_type in acquisition_types
            and t.transaction_date.date() <= income_tx.transaction_date.date()
        )

        # Find total shares sold out of that specific lot.
        sold_from_that_lot = sum(
            s.quantity
            for s in sells
            if s.transaction_date.date() > income_tx.transaction_date.date()
        )

        if bought_at_income_date <= 0:
            continue

        fx_rate = (
            Decimal(str(income_tx.details.get("fx_rate", 1)))
            if income_tx.details
            else Decimal(1)
        )

        # COUPON amount is in quantity, DIVIDEND amount is quantity * price
        if income_tx.transaction_type == "COUPON":
            amount = float(income_tx.quantity * fx_rate)
        else:
            amount = float(income_tx.quantity * income_tx.price_per_unit * fx_rate)

        # Correct proration: based on shares sold out of the total held at the time.
        proportion_realized = float(sold_from_that_lot / bought_at_income_date)
        proportion_unrealized = 1.0 - proportion_realized

        realized_income = amount * proportion_realized
        unrealized_income = amount * proportion_unrealized

        realized_cash_flows.append((income_tx.transaction_date.date(), realized_income))
        unrealized_cash_flows.append(
            (income_tx.transaction_date.date(), unrealized_income)
        )

    # Contributions (like for PPF) are outflows and are always part of the
    # "unrealized" stream as they can't be "sold".
    for contrib_tx in contribution_flows:
        amount = float(-contrib_tx.quantity)
        # Add to unrealized flows for "Current XIRR"
        unrealized_cash_flows.append((contrib_tx.transaction_date.date(), amount))
        # Also add to realized flows to ensure "Historical XIRR" is correct
        realized_cash_flows.append((contrib_tx.transaction_date.date(), amount))

    return realized_cash_flows, unrealized_cash_flows


def _calculate_xirr_from_cashflows_tuple(
    cash_flows: List[Tuple[date, float]],
) -> float:
    """A generic XIRR calculation helper for tuple-based cashflows."""
    if not cash_flows:
        return 0.0
    dates, values = zip(*cash_flows)
    return _calculate_xirr(list(dates), [Decimal(str(v)) for v in values])


def _get_portfolio_cash_flows(
    transactions: List[Transaction],
    all_fixed_deposits: List[FixedDeposit],
    all_recurring_deposits: List[RecurringDeposit],
) -> List[Tuple[date, Decimal]]:
    """
    Generates a unified list of cash flow tuples (date, amount) for an entire portfolio.
    """
    cash_flows = []

    # 1. Cashflows from standard transactions (Stocks, MFs, PPF, etc.)
    for tx in transactions:
        behavior = TRANSACTION_BEHAVIORS.get(tx.transaction_type)
        # For portfolio-level XIRR, we ignore internal accruals like PPF interest.
        # These are not true external cash flows and are captured in the
        # final current_value of the holding.
        # We explicitly include COUPON and DIVIDEND as they are external cash inflows.
        if (
            not behavior
            or behavior["cash_flow"] == CashFlowType.NONE
            or tx.transaction_type == "INTEREST_CREDIT"
        ):
            continue

        # Skip BUY transactions from corporate actions
        if tx.details and tx.details.get("from_merger"):
            continue
        if tx.details and tx.details.get("from_demerger"):
            continue
        if tx.details and tx.details.get("from_rename"):
            continue

        amount = Decimal("0.0")
        fx_rate = (
            Decimal(str(tx.details.get("fx_rate", 1)))
            if tx.details
            else Decimal(1)
        )

        if tx.transaction_type == "CONTRIBUTION":
            # For PPF contributions, the 'quantity' is the amount.
            amount = tx.quantity
        elif tx.transaction_type == "COUPON":
            # For coupons, the 'quantity' is the total amount, and price is 1.
            amount = tx.quantity * fx_rate
        elif tx.transaction_type == "RSU_VEST":
            # For RSU VEST, outflow is FMV * Quantity * FX Rate
             fmv = Decimal(str(tx.details.get("fmv", 0))) if tx.details else Decimal(0)
             amount = tx.quantity * fmv * fx_rate
        else:
            amount = tx.quantity * tx.price_per_unit * fx_rate

        cash_flow_direction = Decimal(behavior["cash_flow"].value)
        cash_flows.append((tx.transaction_date.date(), amount * cash_flow_direction))

    # 2. Cashflows from Fixed Deposits
    for fd in all_fixed_deposits:
        # Initial investment is an outflow
        cash_flows.append((fd.start_date, -fd.principal_amount))

        # For non-cumulative FDs, interest payments are inflows
        if fd.interest_payout != "Cumulative":
            payout_frequency_map = {
                "MONTHLY": 1, "QUARTERLY": 3, "HALF_YEARLY": 6,
                "SEMI-ANNUALLY": 6, "ANNUALLY": 12
            }
            months_interval = payout_frequency_map.get(
                fd.compounding_frequency.upper())
            if months_interval:
                payouts_per_year = Decimal("12.0") / Decimal(str(months_interval))
                payout_rate = fd.interest_rate / Decimal("100.0") / payouts_per_year
                interest_per_payout = fd.principal_amount * payout_rate

                payout_date = fd.start_date + relativedelta(months=months_interval)
                while payout_date <= date.today() and payout_date <= fd.maturity_date:
                    cash_flows.append((payout_date, interest_per_payout))
                    payout_date += relativedelta(months=months_interval)

    # 3. Cashflows from Recurring Deposits
    for rd in all_recurring_deposits:
        # Each installment is an outflow
        for i in range(rd.tenure_months):
            installment_date = rd.start_date + relativedelta(months=i)
            if installment_date > date.today():
                break
            cash_flows.append((installment_date, -rd.monthly_installment))

    # Sort by date to ensure correct XIRR calculation
    cash_flows.sort(key=lambda x: x[0])
    return cash_flows


class CRUDAnalytics:
    @cache_analytics_data(prefix="analytics:asset_analytics", arg_names=["asset_id"])
    def get_asset_analytics(
        self, db: Session, *, portfolio_id: uuid.UUID, asset_id: uuid.UUID
    ) -> schemas.AssetAnalytics:
        """Calculates analytics for a single asset in a portfolio."""
        asset = crud.asset.get(db, id=asset_id)
        if not asset:
            logger.warning(f"Asset with ID {asset_id} not found.")
            return schemas.AssetAnalytics(xirr_current=0.0, xirr_historical=0.0)
        logger.debug(
            f"Calculating analytics for asset {asset_id} ({asset.ticker_symbol})"
        )

        # We need the current value of the holding, which is calculated in crud_holding
        all_holdings_data = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio_id
        )
        holding = next(
            (h for h in all_holdings_data.holdings if h.asset_id == asset_id), None
        )
        if not holding:
            logger.debug(f"No active holding found for asset {asset_id}.")
            return schemas.AssetAnalytics(xirr_current=0.0, xirr_historical=0.0)

        transactions = crud.transaction.get_multi_by_portfolio_and_asset(
            db, portfolio_id=portfolio_id, asset_id=asset_id
        )

        transactions_schemas = [
            schemas.Transaction.model_validate(tx) for tx in transactions
        ]
        realized_cfs, unrealized_cfs = _get_realized_and_unrealized_cash_flows(
            transactions_schemas
        )

        # --- Calculate Current XIRR (for open positions) ---
        xirr_current_cfs = list(unrealized_cfs)
        if holding.current_value > 0:
            xirr_current_cfs.append((date.today(), float(holding.current_value)))
        xirr_current_value = _calculate_xirr_from_cashflows_tuple(xirr_current_cfs)

        # --- Calculate Historical XIRR (for all positions) ---
        if asset.asset_type == "PPF":
            # For PPF, historical and current XIRR are the same.
            xirr_historical_value = xirr_current_value
        else:
            xirr_historical_cfs = list(realized_cfs) + list(unrealized_cfs)
            if holding.current_value > 0:
                xirr_historical_cfs.append((date.today(), float(holding.current_value)))
            xirr_historical_value = _calculate_xirr_from_cashflows_tuple( # noqa: E501
                xirr_historical_cfs,
            )

        return schemas.AssetAnalytics(
            xirr_current=xirr_current_value, xirr_historical=xirr_historical_value
        )

    def get_fixed_deposit_analytics(
        self, db: Session, *, fd: FixedDeposit
    ) -> schemas.FixedDepositAnalytics:
        """Calculates XIRR for a single Fixed Deposit."""
        # Use the centralized cash flow generator.
        # We pass empty lists for other asset types.
        cash_flows = _get_portfolio_cash_flows(
            transactions=[], all_fixed_deposits=[fd], all_recurring_deposits=[]
        )
        dates, values = zip(*cash_flows) if cash_flows else ([], [])

        today = date.today()
        dates = list(dates)
        values = list(values)

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

        return schemas.FixedDepositAnalytics(
            realized_xirr=realized_xirr,
            unrealized_xirr=unrealized_xirr,
        )

    def get_recurring_deposit_analytics(
        self, db: Session, *, rd: RecurringDeposit
    ) -> schemas.RecurringDepositAnalytics:
        """Calculates XIRR for a single Recurring Deposit."""
        if not rd:
            return schemas.RecurringDepositAnalytics(unrealized_xirr=0.0)

        cash_flows = _get_portfolio_cash_flows(
            transactions=[], all_fixed_deposits=[], all_recurring_deposits=[rd]
        )
        dates, values = zip(*cash_flows) if cash_flows else ([], [])

        today = date.today()
        maturity_date = rd.start_date + relativedelta(months=rd.tenure_months)
        dates = list(dates)
        values = list(values)

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

        xirr_value = _calculate_xirr(dates, values)
        return schemas.RecurringDepositAnalytics(unrealized_xirr=xirr_value)

    @cache_analytics_data(
        prefix="analytics:portfolio_analytics", arg_names=["portfolio_id"]
    )
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

        # Generate a unified list of all cash flows
        cash_flows = _get_portfolio_cash_flows(
            transactions, all_fixed_deposits, all_recurring_deposits
        )
        dates, values = zip(*cash_flows) if cash_flows else ([], [])

        # Add current portfolio value as the final cashflow
        # Per FR6.2, the final value for XIRR must be the market value of assets,
        # not the total_value which includes cash from income (which is already
        # accounted for as a separate cash flow).
        current_market_value = sum(h.current_value for h in holdings_data.holdings)
        if current_market_value > 0:
            dates = list(dates) + [date.today()]
            values = list(values) + [current_market_value]

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

        history_points = _get_portfolio_history(
            db=db, user=user, portfolio_id=portfolio_id, range_str="all"
        )
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
    ).summary
    return summary.total_value


def _get_asset_current_value(
    db: Session, portfolio_id: uuid.UUID, asset_id: uuid.UUID
) -> Decimal:
    """Helper to get the current value of a single asset in a portfolio."""
    holdings = crud.holding.get_portfolio_holdings_and_summary(
        db, portfolio_id=portfolio_id
    ).holdings
    for h in holdings:
        if h.asset_id == asset_id:
            return h.current_value
    return Decimal("0.0")


analytics = CRUDAnalytics()

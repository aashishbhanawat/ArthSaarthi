import logging
import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.services.financial_data_service import financial_data_service

logger = logging.getLogger(__name__)


def _calculate_fd_current_value(
    principal: Decimal,
    interest_rate: Decimal,
    start_date: date,
    end_date: date,
    compounding_frequency: str,
    interest_payout: str,
) -> Decimal:
    """
    Calculates the current value of an FD.
    For cumulative FDs, it uses compound interest.
    For payout FDs, it returns the principal.
    """
    if interest_payout != "Cumulative":
        return principal

    if end_date < start_date:
        return principal

    compounding_frequency_map = {
        "Annually": 1,
        "Semi-Annually": 2,
        "Quarterly": 4,
        "Monthly": 12,
    }
    n = Decimal(compounding_frequency_map.get(compounding_frequency, 1))

    t = Decimal((end_date - start_date).days / 365.25)
    r = Decimal(interest_rate / 100)
    current_value = principal * ((1 + r / n) ** (n * t))
    return current_value


def _calculate_total_interest_paid(fd: models.FixedDeposit, end_date: date) -> Decimal:
    """Calculates the total interest paid for a payout FD up to a given end date."""
    if fd.interest_payout == "Cumulative":
        return Decimal(0)

    payout_frequency_map = {
        "MONTHLY": 1,
        "QUARTERLY": 3,
        "HALF_YEARLY": 6,
        "SEMI-ANNUALLY": 6,  # Alias for compatibility
        "ANNUALLY": 12,
    }
    months_interval = payout_frequency_map.get(fd.compounding_frequency.upper())

    if not months_interval:
        return Decimal(0)

    payouts_per_year = Decimal("12.0") / Decimal(str(months_interval))
    payout_rate = fd.interest_rate / Decimal("100.0") / payouts_per_year
    interest_per_payout = fd.principal_amount * payout_rate

    total_interest = Decimal(0)
    payout_date = fd.start_date + relativedelta(months=months_interval)
    while payout_date <= end_date:
        total_interest += interest_per_payout
        payout_date += relativedelta(months=months_interval)
    return total_interest


def _calculate_rd_value_at_date(
    monthly_installment: Decimal,
    interest_rate: Decimal,
    start_date: date,
    tenure_months: int,
    calculation_date: date,
) -> Decimal:
    """
    Calculates the value of a recurring deposit at a specific date by summing the future value of each installment.
    """
    total_value = Decimal("0.0")
    annual_rate = interest_rate / Decimal("100")
    n = Decimal(4)  # Compounding quarterly

    current_installment_date = start_date
    installments_paid = 0

    while installments_paid < tenure_months:
        # Only calculate for installments paid up to the calculation_date
        if current_installment_date > calculation_date:
            break

        t_years = Decimal((calculation_date - current_installment_date).days) / Decimal(
            "365.25"
        )
        fv_of_installment = monthly_installment * (
            (Decimal(1) + annual_rate / n) ** (n * t_years)
        )
        total_value += fv_of_installment

        current_installment_date += relativedelta(months=1)
        installments_paid += 1

    return total_value


class CRUDHolding:
    """
    CRUD operations for portfolio holdings.
    This is a read-only CRUD module that calculates holdings based on transactions.
    """

    def get_portfolio_holdings_and_summary(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Calculates the consolidated holdings and a summary for a given portfolio.
        """
        transactions = crud.transaction.get_multi_by_portfolio(
            db=db, portfolio_id=portfolio_id
        )
        all_fixed_deposits = crud.fixed_deposit.get_multi_by_portfolio(
            db=db, portfolio_id=portfolio_id
        )
        all_recurring_deposits = crud.recurring_deposit.get_multi_by_portfolio(
            db=db, portfolio_id=portfolio_id
        )

        holdings_list: List[schemas.Holding] = []
        summary_total_value = Decimal("0.0")
        summary_total_invested = Decimal("0.0")
        summary_days_pnl = Decimal("0.0")
        total_realized_pnl = Decimal("0.0")

        active_fixed_deposits = [
            fd for fd in all_fixed_deposits if fd.maturity_date >= date.today()
        ]
        matured_fixed_deposits = [
            fd for fd in all_fixed_deposits if fd.maturity_date < date.today()
        ]

        for fd in matured_fixed_deposits:
            if fd.interest_payout != "Cumulative":
                total_realized_pnl += _calculate_total_interest_paid(
                    fd, fd.maturity_date
                )
            else:
                maturity_value = _calculate_fd_current_value(
                    fd.principal_amount,
                    fd.interest_rate,
                    fd.start_date,
                    fd.maturity_date, # Use maturity date for final value
                    fd.compounding_frequency,
                    fd.interest_payout,
                )
                total_realized_pnl += maturity_value - fd.principal_amount

        for fd in active_fixed_deposits:
            total_interest_paid = _calculate_total_interest_paid(fd, date.today())
            if total_interest_paid > 0:
                total_realized_pnl += total_interest_paid

            current_value = _calculate_fd_current_value(
                fd.principal_amount,
                fd.interest_rate,
                fd.start_date,
                date.today(),
                fd.compounding_frequency,
                fd.interest_payout,
            )
            unrealized_pnl = current_value - fd.principal_amount
            unrealized_pnl_percentage = (
                float(unrealized_pnl / fd.principal_amount)
                if fd.principal_amount > 0
                else 0.0
            )
            holdings_list.append(
                schemas.Holding(
                    asset_id=fd.id,
                    ticker_symbol=fd.account_number,
                    asset_name=fd.name,
                    asset_type="FIXED_DEPOSIT",
                    group="DEPOSITS",
                    quantity=Decimal(1),
                    average_buy_price=fd.principal_amount,
                    total_invested_amount=fd.principal_amount,
                    current_price=current_value,
                    current_value=current_value,
                    days_pnl=Decimal(0),
                    days_pnl_percentage=0.0,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percentage=unrealized_pnl_percentage,
                    realized_pnl=total_interest_paid,
                    interest_rate=fd.interest_rate,
                    maturity_date=fd.maturity_date,
                    account_number=fd.account_number,
                )
            )
            summary_total_value += current_value
            summary_total_invested += fd.principal_amount

        # --- Recurring Deposits ---
        today = date.today()
        active_recurring_deposits = [
            rd
            for rd in all_recurring_deposits
            if (rd.start_date + relativedelta(months=rd.tenure_months)) >= today
        ]
        matured_recurring_deposits = [
            rd
            for rd in all_recurring_deposits
            if (rd.start_date + relativedelta(months=rd.tenure_months)) < today
        ]

        for rd in matured_recurring_deposits:
            maturity_date = rd.start_date + relativedelta(months=rd.tenure_months)
            maturity_value = _calculate_rd_value_at_date(
                rd.monthly_installment,
                rd.interest_rate,
                rd.start_date,
                rd.tenure_months,
                maturity_date,
            )
            total_invested = rd.monthly_installment * rd.tenure_months
            total_realized_pnl += maturity_value - total_invested

        for rd in active_recurring_deposits:
            current_value = _calculate_rd_value_at_date(
                rd.monthly_installment,
                rd.interest_rate,
                rd.start_date,
                rd.tenure_months,
                today,
            )

            installments_paid = 0
            temp_date = rd.start_date
            while temp_date <= today and installments_paid < rd.tenure_months:
                installments_paid += 1
                temp_date += relativedelta(months=1)

            total_invested = rd.monthly_installment * installments_paid
            if total_invested <= 0:
                continue

            unrealized_pnl = current_value - total_invested
            unrealized_pnl_percentage = (
                float(unrealized_pnl / total_invested) if total_invested > 0 else 0.0
            )

            holdings_list.append(
                schemas.Holding(
                    asset_id=rd.id,
                    asset_name=rd.name,
                    asset_type="RECURRING_DEPOSIT",
                    group="DEPOSITS",
                    quantity=Decimal(1),
                    total_invested_amount=total_invested,
                    current_price=current_value,
                    current_value=current_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percentage=unrealized_pnl_percentage,
                    interest_rate=rd.interest_rate,
                    maturity_date=rd.start_date
                    + relativedelta(months=rd.tenure_months),
                )
            )
            summary_total_value += current_value
            summary_total_invested += total_invested

        if not transactions:
            summary = schemas.PortfolioSummary(
                total_value=summary_total_value,
                total_invested_amount=summary_total_invested,
                days_pnl=summary_days_pnl,
                total_unrealized_pnl=summary_total_value - summary_total_invested,
                total_realized_pnl=total_realized_pnl,
            )
            return {"summary": summary, "holdings": holdings_list}

        transactions.sort(key=lambda tx: tx.transaction_date)

        holdings_state = defaultdict(
            lambda: {"quantity": Decimal("0.0"), "total_invested": Decimal("0.0")}
        )
        asset_map = {tx.asset.ticker_symbol: tx.asset for tx in transactions}

        for tx in transactions:
            ticker = tx.asset.ticker_symbol
            if tx.transaction_type == "BUY":
                holdings_state[ticker]["quantity"] += tx.quantity
                holdings_state[ticker]["total_invested"] += (
                    tx.quantity * tx.price_per_unit
                )
            elif tx.transaction_type == "SELL":
                if holdings_state[ticker]["quantity"] > 0:
                    avg_buy_price = (
                        holdings_state[ticker]["total_invested"]
                        / holdings_state[ticker]["quantity"]
                    )
                    realized_pnl_for_sale = (
                        tx.price_per_unit - avg_buy_price
                    ) * tx.quantity
                    total_realized_pnl += realized_pnl_for_sale
                    proportion_sold = tx.quantity / holdings_state[ticker]["quantity"]
                    holdings_state[ticker]["total_invested"] *= 1 - proportion_sold
                    holdings_state[ticker]["quantity"] -= tx.quantity

        current_holdings_tickers = [
            ticker for ticker, data in holdings_state.items() if data["quantity"] > 0
        ]

        assets_to_price = [
            {
                "ticker_symbol": ticker,
                "exchange": asset_map[ticker].exchange,
                "asset_type": asset_map[ticker].asset_type,
            }
            for ticker in current_holdings_tickers
            if ticker in asset_map
        ]

        if assets_to_price:
            price_details = financial_data_service.get_current_prices(assets_to_price)
        else:
            price_details = {}

        for ticker in current_holdings_tickers:
            asset = asset_map[ticker]
            data = holdings_state[ticker]
            price_info = price_details.get(
                ticker, {"current_price": Decimal(0), "previous_close": Decimal(0)}
            )
            current_price = price_info["current_price"]
            previous_close = price_info["previous_close"]

            quantity = data["quantity"]
            total_invested = data["total_invested"]
            average_buy_price = (
                total_invested / quantity if quantity > 0 else Decimal(0)
            )
            current_value = quantity * current_price
            unrealized_pnl = current_value - total_invested
            unrealized_pnl_percentage = (
                float(unrealized_pnl / total_invested)
                if total_invested > 0
                else 0.0
            )
            days_pnl = (current_price - previous_close) * quantity
            days_pnl_percentage = (
                float((current_price - previous_close) / previous_close)
                if previous_close > 0
                else 0.0
            )

            group_map = {
                "STOCK": "EQUITIES",
                "MUTUAL_FUND": "EQUITIES",
                "ETF": "EQUITIES",
                "FIXED_DEPOSIT": "DEPOSITS",
                "BOND": "BONDS",
                "PPF": "SCHEMES",
                "Mutual Fund": "EQUITIES",
            }
            group = group_map.get(
                asset.asset_type.upper().replace(" ", "_"), "MISCELLANEOUS"
            )

            holdings_list.append(
                schemas.Holding(
                    asset_id=asset.id,
                    ticker_symbol=ticker,
                    asset_name=asset.name,
                    asset_type=asset.asset_type,
                    group=group,
                    quantity=quantity,
                    average_buy_price=average_buy_price,
                    total_invested_amount=total_invested,
                    current_price=current_price,
                    current_value=current_value,
                    days_pnl=days_pnl,
                    days_pnl_percentage=days_pnl_percentage,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percentage=unrealized_pnl_percentage,
                )
            )
            summary_total_value += current_value
            summary_total_invested += total_invested
            summary_days_pnl += days_pnl

        summary = schemas.PortfolioSummary(
            total_value=summary_total_value,
            total_invested_amount=summary_total_invested,
            days_pnl=summary_days_pnl,
            total_unrealized_pnl=summary_total_value - summary_total_invested,
            total_realized_pnl=total_realized_pnl,
        )

        return {"summary": summary, "holdings": holdings_list}


holding = CRUDHolding()

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
    Calculates the value of a recurring deposit at a specific date by calculating
    the future value of each installment.
    """
    if calculation_date < start_date:
        return Decimal("0.0")

    total_value = Decimal("0.0")
    r = interest_rate / Decimal("100.0")
    n = Decimal("4.0")  # Quarterly compounding

    # Iterate through each month an installment is made
    for i in range(tenure_months):
        installment_date = start_date + relativedelta(months=i)

        if installment_date > calculation_date:
            break

        # Calculate the time in years from the installment date to the calculation date
        days_to_grow = (calculation_date - installment_date).days
        t = Decimal(str(days_to_grow / 365.25))

        # Future value of this single installment
        fv_installment = monthly_installment * ((1 + r / n) ** (n * t))
        total_value += fv_installment

    return total_value


class CRUDHolding:
    """
    CRUD operations for portfolio holdings.
    This is a read-only CRUD module that calculates holdings based on transactions.
    """

    def _calculate_and_apply_ppf_interest(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> None:
        """
        Calculates and applies PPF interest for completed financial years.
        This method has side effects (creates transactions) and is called before
        calculating holdings.
        """
        all_transactions = crud.transaction.get_multi_by_portfolio(
            db=db, portfolio_id=portfolio_id
        )

        ppf_assets = {
            tx.asset for tx in all_transactions if tx.asset.asset_type.upper() == "PPF"
        }

        for asset in ppf_assets:
            asset_transactions = sorted(
                [tx for tx in all_transactions if tx.asset_id == asset.id],
                key=lambda tx: tx.transaction_date,
            )

            if not asset_transactions:
                continue

            start_date = asset.opening_date
            end_date = date.today()

            start_fy = start_date.year if start_date.month > 3 else start_date.year - 1
            end_fy = end_date.year if end_date.month > 3 else end_date.year - 1

            for year in range(start_fy, end_fy):
                fy_start = date(year, 4, 1)
                fy_end = date(year + 1, 3, 31)

                # Check if interest for this FY is already credited
                interest_credited = any(
                    tx.transaction_type == "INTEREST_CREDIT"
                    and tx.transaction_date.date() == fy_end
                    for tx in asset_transactions
                )
                if interest_credited:
                    continue

                rate_obj = crud.historical_interest_rate.get_rate_for_date(
                    db, scheme_name="PPF", a_date=fy_start
                )
                if not rate_obj:
                    logger.warning(
                        "No PPF interest rate found for FY %s-%s for asset %s",
                        year,
                        year + 1,
                        asset.id,
                    )
                    continue
                interest_rate = rate_obj.rate

                # Calculate cumulative balance at the start of the financial year
                balance = sum(
                    tx.quantity
                    if tx.transaction_type
                    in ("BUY", "CONTRIBUTION", "INTEREST_CREDIT")
                    else -tx.quantity
                    for tx in asset_transactions
                    if tx.transaction_date.date() < fy_start
                )

                monthly_interest_accrual_base = Decimal("0.0")

                # Iterate from April (4) to March (3 of next year)
                for month_num in range(4, 16):
                    current_year = year if month_num <= 12 else year + 1
                    current_month = month_num if month_num <= 12 else month_num - 12

                    month_start_date = date(current_year, current_month, 1)
                    month_end_date = month_start_date + relativedelta(
                        months=1
                    ) - relativedelta(days=1)

                    # Balance at close of 5th day
                    balance_at_5th = balance + sum(
                        tx.quantity
                        if tx.transaction_type in ("BUY", "CONTRIBUTION")
                        else -tx.quantity
                        for tx in asset_transactions
                        if month_start_date
                        <= tx.transaction_date.date()
                        < month_start_date.replace(day=6)
                    )

                    # Balance at end of month
                    balance_at_eom = balance_at_5th + sum(
                        tx.quantity
                        if tx.transaction_type in ("BUY", "CONTRIBUTION")
                        else -tx.quantity
                        for tx in asset_transactions
                        if month_start_date.replace(day=6)
                        <= tx.transaction_date.date()
                        <= month_end_date
                    )

                    monthly_interest_accrual_base += min(balance_at_5th, balance_at_eom)
                    balance = balance_at_eom

                interest_for_fy = (
                    monthly_interest_accrual_base * interest_rate
                ) / (Decimal("12") * Decimal("100"))
                interest_for_fy = round(interest_for_fy, 0)

                if interest_for_fy > 0:
                    interest_tx_in = schemas.TransactionCreate(
                        asset_id=asset.id,
                        transaction_type="INTEREST_CREDIT",
                        quantity=interest_for_fy,
                        price_per_unit=1,
                        transaction_date=fy_end,
                    )
                    created_tx = crud.transaction.create_with_portfolio(
                        db, obj_in=interest_tx_in, portfolio_id=portfolio_id
                    )
                    # Add to asset_transactions for subsequent calculations
                    asset_transactions.append(created_tx)
                    asset_transactions.sort(key=lambda tx: tx.transaction_date)
        db.commit()

    def get_portfolio_holdings_and_summary(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Calculates the consolidated holdings and a summary for a given portfolio.
        """
        self._calculate_and_apply_ppf_interest(db, portfolio_id=portfolio_id)

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
                    fd.maturity_date,  # Use maturity date for final value
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
                    average_buy_price=total_invested,
                    total_invested_amount=total_invested,
                    current_price=current_value,
                    current_value=current_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percentage=unrealized_pnl_percentage,
                    interest_rate=rd.interest_rate,
                    maturity_date=rd.start_date
                    + relativedelta(months=rd.tenure_months),
                    ticker_symbol=rd.account_number or rd.name,
                    account_number=rd.account_number,
                    days_pnl=Decimal(0),
                    days_pnl_percentage=0.0,
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
            lambda: {
                "quantity": Decimal("0.0"),
                "total_invested": Decimal("0.0"),
                "realized_pnl": Decimal("0.0"),
            }
        )
        asset_map = {tx.asset.ticker_symbol: tx.asset for tx in transactions}

        for tx in transactions:
            ticker = tx.asset.ticker_symbol
            if tx.transaction_type in ("BUY", "CONTRIBUTION"):
                holdings_state[ticker]["quantity"] += tx.quantity
                holdings_state[ticker]["total_invested"] += (
                    tx.quantity * tx.price_per_unit
                )
            elif tx.transaction_type == "INTEREST_CREDIT":
                holdings_state[ticker]["quantity"] += tx.quantity
                # Interest is not an investment, but adds to the value
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

            # For PPF, current price is always 1
            if asset.asset_type.upper() == "PPF":
                price_info = {
                    "current_price": Decimal(1),
                    "previous_close": Decimal(1),
                }
            else:
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
                float(unrealized_pnl / total_invested) if total_invested > 0 else 0.0
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

import logging
import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.crud.crud_ppf import process_ppf_holding
from app.models.recurring_deposit import RecurringDeposit
from app.schemas.enums import BondType
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
    # Standard formula for RD maturity value with quarterly compounding.
    # M = P * [((1 + r/n)^(n*t) - 1) / (1 - (1+r/n)^(-1/3))]
    # where n=4 for quarterly. This iterative approach is equivalent and clearer.
    total_value = Decimal("0.0")
    quarterly_rate = interest_rate / Decimal("400.0")  # r/n where n=4, and r is in %

    num_installments = min(
        tenure_months,
        (calculation_date.year - start_date.year) * 12
        + (calculation_date.month - start_date.month)
        + 1,
    )

    for i in range(num_installments):
        _ = start_date + relativedelta(months=i)
        num_quarters = Decimal(num_installments - i) / 3
        total_value += monthly_installment * (1 + quarterly_rate) ** num_quarters

    return total_value.quantize(Decimal("0.01"))


def _process_fixed_deposits(
    all_fixed_deposits: List[models.FixedDeposit],
) -> tuple[list[schemas.Holding], Decimal]:
    """Processes all fixed deposits, separating active and matured ones."""
    holdings_list = []
    total_realized_pnl = Decimal("0.0")
    today = date.today()

    active_fds = [fd for fd in all_fixed_deposits if fd.maturity_date >= today]
    matured_fds = [fd for fd in all_fixed_deposits if fd.maturity_date < today]

    for fd in matured_fds:
        if fd.interest_payout != "Cumulative":
            total_realized_pnl += _calculate_total_interest_paid(fd, fd.maturity_date)
        else:
            maturity_value = _calculate_fd_current_value(
                fd.principal_amount,
                fd.interest_rate,
                fd.start_date,
                fd.maturity_date,
                fd.compounding_frequency,
                fd.interest_payout,
            )
            total_realized_pnl += maturity_value - fd.principal_amount

    for fd in active_fds:
        interest_paid_to_date = _calculate_total_interest_paid(fd, today)
        if interest_paid_to_date > 0:
            total_realized_pnl += interest_paid_to_date

        current_value = _calculate_fd_current_value(
            fd.principal_amount,
            fd.interest_rate,
            fd.start_date,
            today,
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
                realized_pnl=interest_paid_to_date,
                interest_rate=fd.interest_rate,
                maturity_date=fd.maturity_date,
                account_number=fd.account_number,
            )
        )
    return holdings_list, total_realized_pnl


def _process_recurring_deposits(
    all_recurring_deposits: List[RecurringDeposit],
) -> tuple[list[schemas.Holding], Decimal]:
    """Processes all recurring deposits, separating active and matured ones."""
    holdings_list = []
    total_realized_pnl = Decimal("0.0")
    today = date.today()

    active_rds = [
        rd
        for rd in all_recurring_deposits
        if (rd.start_date + relativedelta(months=rd.tenure_months)) >= today
    ]
    matured_rds = [
        rd
        for rd in all_recurring_deposits
        if (rd.start_date + relativedelta(months=rd.tenure_months)) < today
    ]

    for rd in matured_rds:
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

    for rd in active_rds:
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
                maturity_date=rd.start_date + relativedelta(months=rd.tenure_months),
                ticker_symbol=rd.account_number or rd.name,
                account_number=rd.account_number,
                days_pnl=Decimal(0),
                days_pnl_percentage=0.0,
            )
        )
    return holdings_list, total_realized_pnl


def _calculate_summary(
    holdings_list: List[schemas.Holding],
    realized_pnl_from_other_sources: Decimal,
    transactions: List[models.Transaction],
) -> schemas.PortfolioSummary:
    """Calculates the final portfolio summary from a list of holdings."""
    summary_total_value = Decimal("0.0")
    summary_total_invested = Decimal("0.0")
    summary_days_pnl = Decimal("0.0")
    summary_total_unrealized_pnl = Decimal("0.0")

    for holding_item in holdings_list:
        summary_total_value += holding_item.current_value
        summary_total_invested += holding_item.total_invested_amount
        summary_total_unrealized_pnl += holding_item.unrealized_pnl
        summary_days_pnl += holding_item.days_pnl

    income_cash = sum(
        tx.quantity * tx.price_per_unit
        for tx in transactions
        if tx.transaction_type in ["DIVIDEND", "COUPON"]
    )
    summary_total_value += income_cash

    return schemas.PortfolioSummary(
        total_value=summary_total_value,
        total_invested_amount=summary_total_invested,
        days_pnl=summary_days_pnl,
        total_unrealized_pnl=summary_total_unrealized_pnl,
        total_realized_pnl=realized_pnl_from_other_sources,
    )


def _process_market_traded_assets(
    db: Session,
    portfolio_id: uuid.UUID,
    transactions: List[models.Transaction],
    initial_realized_pnl: Decimal,
) -> tuple[List[schemas.Holding], Decimal]:
    """Processes all market-traded assets like Stocks, MFs, ETFs, and Bonds."""
    holdings_list = []
    total_realized_pnl = initial_realized_pnl

    holdings_state = defaultdict(
        lambda: {
            "quantity": Decimal("0.0"),
            "total_invested": Decimal("0.0"),
            "realized_pnl": Decimal("0.0"),
        }
    )

    portfolio_assets = crud.asset.get_multi_by_portfolio(db, portfolio_id=portfolio_id)
    asset_map = {asset.ticker_symbol: asset for asset in portfolio_assets}

    for tx in transactions:
        asset = asset_map.get(tx.asset.ticker_symbol) if tx.asset else None
        if not asset:
            asset = next((a for a in portfolio_assets if a.id == tx.asset_id), None)
        ticker = asset.ticker_symbol if asset else None
        if tx.transaction_type == "BUY":
            holdings_state[ticker]["quantity"] += tx.quantity
            holdings_state[ticker]["total_invested"] += tx.quantity * tx.price_per_unit
        elif tx.transaction_type == "DIVIDEND":
            dividend_amount = tx.quantity * tx.price_per_unit
            total_realized_pnl += dividend_amount
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
                holdings_state[ticker]["realized_pnl"] += realized_pnl_for_sale
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
    ]

    price_details = (
        financial_data_service.get_current_prices(assets_to_price)
        if assets_to_price
        else {}
    )

    for ticker in current_holdings_tickers:
        asset = asset_map[ticker]
        data = holdings_state[ticker]
        price_info = price_details.get(
            ticker, {"current_price": Decimal(0), "previous_close": Decimal(0)}
        )

        quantity = data["quantity"]
        total_invested = data["total_invested"]

        days_pnl = Decimal("0.0")
        if asset.asset_type == "BOND" and asset.bond:
            bond_details = asset.bond
            current_price = Decimal(str(price_info["current_price"]))

            if current_price == 0 and asset.ticker_symbol:
                yf_price = financial_data_service.get_price_from_yfinance(
                    asset.ticker_symbol
                )
                if yf_price:
                    current_price = yf_price

            if current_price == 0 and bond_details.bond_type == BondType.TBILL:
                first_buy = min(
                    (
                        tx
                        for tx in transactions
                        if tx.asset_id == asset.id and tx.transaction_type == "BUY"
                    ),
                    key=lambda x: x.transaction_date,
                    default=None,
                )
                if first_buy and bond_details.face_value:
                    purchase_date = first_buy.transaction_date.date()
                    total_days = (bond_details.maturity_date - purchase_date).days
                    days_elapsed = (date.today() - purchase_date).days
                    if total_days > 0 and days_elapsed > 0:
                        price_increase = (
                            Decimal(str(bond_details.face_value))
                            - first_buy.price_per_unit
                        ) * (Decimal(days_elapsed) / Decimal(total_days))
                        current_price = first_buy.price_per_unit + price_increase

            if current_price == 0:
                current_price = (
                    total_invested / quantity if quantity > 0 else Decimal(0)
                )
                price_info["previous_close"] = current_price.quantize(Decimal("0.01"))
        else:
            current_price = Decimal(str(price_info["current_price"]))

        previous_close = Decimal(str(price_info["previous_close"]))
        average_buy_price = total_invested / quantity if quantity > 0 else Decimal(0)
        days_pnl = (current_price - previous_close) * quantity
        days_pnl_percentage = (
            float((current_price - previous_close) / previous_close)
            if previous_close > 0
            else 0.0
        )
        current_value = quantity * current_price

        holdings_list.append(
            schemas.Holding(
                asset_id=asset.id,
                ticker_symbol=ticker,
                asset_name=asset.name,
                asset_type=asset.asset_type,
                group="EQUITIES",  # Placeholder, will be set properly later
                quantity=quantity,
                average_buy_price=average_buy_price,
                total_invested_amount=total_invested,
                current_price=current_price,
                current_value=current_value,
                days_pnl=days_pnl,
                days_pnl_percentage=days_pnl_percentage,
                unrealized_pnl=Decimal("0.0"),
                realized_pnl=data.get("realized_pnl", Decimal("0.0")),
                unrealized_pnl_percentage=0.0,
                bond=asset.bond,
            )
        )
    return holdings_list, total_realized_pnl


class CRUDHolding:
    """
    CRUD operations for portfolio holdings.
    This is a read-only CRUD module that calculates holdings based on transactions.
    """

    def get_portfolio_holdings_and_summary(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Calculates the consolidated holdings and a summary for a given portfolio."""
        transactions = crud.transaction.get_multi_by_portfolio(
            db=db, portfolio_id=portfolio_id
        )
        all_fixed_deposits = crud.fixed_deposit.get_multi_by_portfolio(
            db, portfolio_id=portfolio_id
        )
        all_recurring_deposits = crud.recurring_deposit.get_multi_by_portfolio(
            db=db, portfolio_id=portfolio_id
        )

        # --- Process Non-Market-Traded Assets ---
        fd_holdings, pnl_from_fds = _process_fixed_deposits(all_fixed_deposits)
        rd_holdings, pnl_from_rds = _process_recurring_deposits(
            all_recurring_deposits
        )
        holdings_list: List[schemas.Holding] = fd_holdings + rd_holdings
        total_realized_pnl = pnl_from_fds + pnl_from_rds

        # --- PPF Holdings ---
        all_portfolio_assets = crud.asset.get_multi_by_portfolio(
            db, portfolio_id=portfolio_id
        )
        ppf_assets = [
            asset for asset in all_portfolio_assets if asset.asset_type.upper() == "PPF"
        ]
        for ppf_asset in ppf_assets:
            # Lock the asset row before processing to prevent race conditions
            # on the interest calculation logic, which has a write side-effect.
            # This is only supported by PostgreSQL.
            db.query(models.Asset).filter_by(id=ppf_asset.id).with_for_update().first()
            ppf_holding = process_ppf_holding(db, ppf_asset, portfolio_id)
            holdings_list.append(ppf_holding)

        market_traded_holdings, total_realized_pnl = _process_market_traded_assets(
            db, portfolio_id, transactions, total_realized_pnl
        )
        holdings_list.extend(market_traded_holdings)

        # --- Final Grouping and Summary Calculation ---
        for holding_item in holdings_list:
            group_map = {
                "STOCK": "EQUITIES", "Mutual Fund": "EQUITIES", "ETF": "EQUITIES",
                "FIXED_DEPOSIT": "DEPOSITS", "RECURRING_DEPOSIT": "DEPOSITS",
                "BOND": "BONDS", "PPF": "GOVERNMENT_SCHEMES",
            }
            group_map_upper = {k.upper(): v for k, v in group_map.items()}
            holding_item.group = group_map_upper.get(
                str(holding_item.asset_type).upper(), "MISCELLANEOUS")

        summary = _calculate_summary(holdings_list, total_realized_pnl, transactions)

        return {"summary": summary, "holdings": holdings_list}


holding = CRUDHolding()

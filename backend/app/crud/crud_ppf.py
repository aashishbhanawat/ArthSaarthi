import uuid
from datetime import date, timedelta
import logging
from decimal import Decimal
from typing import Any, Dict, List

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models import Asset, Transaction
from app.schemas import AssetType, TransactionType

logger = logging.getLogger(__name__)


def get_financial_year(for_date: date) -> (date, date):
    """Returns the start and end date of the financial year for a given date."""
    if for_date.month >= 4:
        start_date = date(for_date.year, 4, 1)
        end_date = date(for_date.year + 1, 3, 31)
    else:
        start_date = date(for_date.year - 1, 4, 1)
        end_date = date(for_date.year, 3, 31)
    return start_date, end_date


def _calculate_ppf_interest_for_fy(
    db: Session,
    fy_start: date,
    fy_end: date,
    opening_balance: Decimal,
    transactions_in_fy: List[Transaction],
) -> Decimal:
    """Calculates PPF interest for a single financial year using the monthly minimum balance method."""
    total_interest = Decimal("0.0")
    balance_at_start_of_month = opening_balance

    for month_num in range(1, 13):
        current_month_start = fy_start + relativedelta(months=month_num - 1)

        # For on-the-fly calculations, only calculate interest for months that have fully passed.
        if current_month_start >= date.today().replace(day=1):
            break

        current_month_end = current_month_start + relativedelta(months=1)

        # Per PPF rules, interest is calculated on the minimum balance between the 5th and the end of the month.
        # This is the balance at the start of the month, plus any contributions made on or before the 5th.
        balance_for_interest_calc = balance_at_start_of_month
        for t in transactions_in_fy:
            if (
                current_month_start <= t.transaction_date.date() < (current_month_start + timedelta(days=5))
            ) and t.transaction_type == TransactionType.CONTRIBUTION:
                balance_for_interest_calc += t.price_per_unit

        # Get interest rate for the month
        rate_obj = crud.historical_interest_rate.get_rate_for_date(
            db=db, scheme_name="PPF", a_date=current_month_start
        )
        if rate_obj:
            monthly_interest_rate = Decimal(rate_obj.rate) / Decimal("100") / Decimal("12")
            monthly_interest = balance_for_interest_calc * monthly_interest_rate
            total_interest += monthly_interest

        # Update the balance for the start of the next month by adding all contributions from the current month
        for t in transactions_in_fy:
            if (current_month_start <= t.transaction_date.date() < current_month_end) and t.transaction_type == TransactionType.CONTRIBUTION:
                balance_at_start_of_month += t.price_per_unit

    return total_interest.quantize(Decimal("0.01"))

def process_ppf_holding(
    db: Session, ppf_asset: Asset, portfolio_id: uuid.UUID
) -> schemas.Holding:
    """Processes a single PPF asset to calculate its current value and generate interest transactions."""
    transactions = crud.transaction.get_multi_by_asset(db, asset_id=ppf_asset.id)
    transactions.sort(key=lambda t: t.transaction_date)

    opening_date = ppf_asset.opening_date
    if not opening_date:
        # Cannot process without an opening date
        total_contributions = sum(t.price_per_unit for t in transactions if t.transaction_type == TransactionType.CONTRIBUTION)
        return schemas.Holding(
            asset_id=ppf_asset.id,
            ticker_symbol=ppf_asset.ticker_symbol,
            asset_name=ppf_asset.name,
            asset_type=ppf_asset.asset_type,
            quantity=Decimal(1),
            average_buy_price=total_contributions,
            current_price=total_contributions,
            current_value=total_contributions,
            total_invested_amount=total_contributions,
            unrealized_pnl=Decimal(0),
            unrealized_pnl_percentage=0.0,
            realized_pnl=Decimal(0),
            days_pnl=Decimal(0),
            days_pnl_percentage=0.0,
            group="GOVERNMENT_SCHEMES",
        )

    # Separate transactions by type
    contributions = [t for t in transactions if t.transaction_type == TransactionType.CONTRIBUTION]
    interest_credits = {get_financial_year(t.transaction_date.date())[1]: t for t in transactions if t.transaction_type == TransactionType.INTEREST_CREDIT} # type: ignore

    balance = Decimal("0.0")
    total_investment = sum(t.price_per_unit for t in contributions)
    total_credited_interest = Decimal("0.0")
    on_the_fly_interest = Decimal("0.0")

    # Iterate through financial years from opening date
    current_fy_start, _ = get_financial_year(opening_date)
    today = date.today()

    while current_fy_start <= today:
        fy_start, fy_end = get_financial_year(current_fy_start)
        
        transactions_in_fy = [t for t in contributions if fy_start <= t.transaction_date.date() <= fy_end]

        if fy_end < today:  # Completed financial year
            if fy_end in interest_credits: # type: ignore
                interest_for_fy = interest_credits[fy_end].price_per_unit
            else:
                # Calculate and create missing interest transaction
                interest_for_fy = _calculate_ppf_interest_for_fy(db, fy_start, fy_end, balance, transactions_in_fy)
                if interest_for_fy > 0:
                    crud.transaction.create_with_portfolio(
                        db,
                        portfolio_id=portfolio_id,
                        obj_in=schemas.TransactionCreate(
                            asset_id=ppf_asset.id,
                            transaction_type=TransactionType.INTEREST_CREDIT,
                            quantity=1,
                            price_per_unit=interest_for_fy,
                            transaction_date=fy_end.isoformat(),
                        ),
                    )
            total_credited_interest += interest_for_fy
            balance += sum(t.price_per_unit for t in transactions_in_fy if t.transaction_type == TransactionType.CONTRIBUTION) + interest_for_fy
        else:  # Current, ongoing financial year
            on_the_fly_interest = _calculate_ppf_interest_for_fy(db, fy_start, fy_end, balance, transactions_in_fy)
            balance += sum(t.price_per_unit for t in transactions_in_fy if t.transaction_type == TransactionType.CONTRIBUTION) + on_the_fly_interest

        current_fy_start += relativedelta(years=1)

    total_interest_earned = total_credited_interest + on_the_fly_interest
    unrealized_pnl_percentage = (
        (total_interest_earned / total_investment) * 100
        if total_investment > 0
        else Decimal(0)
    )

    return schemas.Holding(
        asset_id=ppf_asset.id,
        ticker_symbol=ppf_asset.ticker_symbol,
        asset_name=ppf_asset.name,
        asset_type=ppf_asset.asset_type,
        quantity=Decimal(1),
        average_buy_price=total_investment,
        current_price=balance,
        current_value=balance,
        total_invested_amount=total_investment,
        unrealized_pnl=on_the_fly_interest,
        realized_pnl=total_credited_interest,
        unrealized_pnl_percentage=float(unrealized_pnl_percentage),
        realized_pl=Decimal(0),
        days_pnl=Decimal(0),
        days_pnl_percentage=0.0,
        group="GOVERNMENT_SCHEMES",
    )


def trigger_ppf_recalculation(db: Session, asset_id: uuid.UUID) -> None:
    """Deletes future interest credits to trigger recalculation."""
    asset = crud.asset.get(db, id=asset_id)
    if not asset or asset.asset_type != AssetType.PPF:
        return

    # This function is called when a contribution is modified.
    # We need to find the financial year of the change and delete all
    # system-generated interest credits from that year onwards.
    # For simplicity in this trigger, we will delete ALL interest credits
    # for the asset. The valuation logic is optimized to only recalculate
    # what's missing, so this is safe and effective.
    
    transactions_to_delete = db.query(Transaction).filter( # type: ignore
        Transaction.asset_id == asset_id,
        Transaction.transaction_type == TransactionType.INTEREST_CREDIT
    ).all()

    if transactions_to_delete:
        logger.info(f"PPF Recalculation: Deleting {len(transactions_to_delete)} old interest credit transactions for asset {asset_id}.")
        for t in transactions_to_delete:
            db.delete(t)
        db.flush()
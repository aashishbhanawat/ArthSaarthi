import logging
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import List

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models import Asset, Transaction
from app.schemas.asset import AssetType
from app.schemas.transaction import TransactionType

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
    """Calculates PPF interest for a single financial year using the monthly minimum balance method."""  # noqa: E501
    logger.debug(
        f"[_calculate_ppf_interest_for_fy] FY: {fy_start}-{fy_end}, "
        f"Opening Balance: {opening_balance}"
    )

    total_interest = Decimal("0.0")
    balance_at_start_of_month = opening_balance

    for month_offset in range(12):
        current_month_start = fy_start + relativedelta(months=month_offset)
        # For on-the-fly calculations, only calculate interest for months that
        # have fully passed. A month has passed if the start of the next month
        # is less than or equal to today's date.
        if (current_month_start + relativedelta(months=1)) > date.today():
            break

        current_month_end = current_month_start + relativedelta(months=1)

        # Per PPF rules, interest is calculated on the minimum balance between
        # the 5th and the end of the month. This is the balance at the start
        # of the month, plus any contributions made on or before the 5th.
        balance_for_interest_calc = balance_at_start_of_month
        for t in transactions_in_fy:
            if (
                current_month_start
                <= t.transaction_date.date()
                < (current_month_start + timedelta(days=5))
            ) and t.transaction_type == TransactionType.CONTRIBUTION:
                balance_for_interest_calc += t.quantity

        # Get interest rate for the month
        rate_obj = crud.historical_interest_rate.get_rate_for_date(
            db=db, scheme_name="PPF", a_date=current_month_start
        )
        if rate_obj:
            monthly_interest_rate = (
                Decimal(rate_obj.rate) / Decimal("100") / Decimal("12")
            )
            monthly_interest = balance_for_interest_calc * monthly_interest_rate
            total_interest += monthly_interest

        # Update the balance for the start of the next month by adding all
        # contributions from the current month
        monthly_contributions_total = Decimal("0.0")
        monthly_contributions_total = sum(
            t.quantity for t in transactions_in_fy if
            current_month_start <= t.transaction_date.date() < current_month_end and
            t.transaction_type == TransactionType.CONTRIBUTION)
        balance_at_start_of_month += monthly_contributions_total

    return total_interest.quantize(Decimal("0.01"))


def _cleanup_duplicate_interest_credits(db: Session, asset_id: uuid.UUID) -> None:
    """
    Removes duplicate interest credits for a PPF asset.
    Keeps the first one (by ID) for each FY and deletes the rest.
    This handles race conditions from concurrent API calls.
    """
    # Get all interest credits for this asset, ordered by date and id
    all_credits = db.query(Transaction).filter(
        Transaction.asset_id == asset_id,
        Transaction.transaction_type == TransactionType.INTEREST_CREDIT,
    ).order_by(Transaction.transaction_date, Transaction.id).all()
    
    if not all_credits:
        return
    
    # Group by FY (based on transaction_date which is the FY end date)
    seen_fy_dates = set()
    duplicates_to_delete = []
    
    for credit in all_credits:
        fy_date = credit.transaction_date.date()
        if fy_date in seen_fy_dates:
            duplicates_to_delete.append(credit)
        else:
            seen_fy_dates.add(fy_date)
    
    if duplicates_to_delete:
        logger.info(
            f"[PPF] Cleaning up {len(duplicates_to_delete)} duplicate "
            f"interest credits for asset {asset_id}"
        )
        for dup in duplicates_to_delete:
            db.delete(dup)
        db.commit()

def process_ppf_holding(
    db: Session, ppf_asset: Asset, portfolio_id: uuid.UUID
) -> schemas.Holding:
    """Processes a single PPF asset to calculate its current value and generate interest transactions."""  # noqa: E501
    transactions = crud.transaction.get_multi_by_asset(db, asset_id=ppf_asset.id)
    logger.debug(
        f"[process_ppf_holding] Processing asset {ppf_asset.id}, "
        f"found {len(transactions)} transactions."
    )
    transactions.sort(key=lambda t: t.transaction_date)

    opening_date = ppf_asset.opening_date
    if not opening_date:
        # Cannot process without an opening date
        total_contributions = sum(
            t.quantity
            for t in transactions
            if t.transaction_type == TransactionType.CONTRIBUTION
        )
        return schemas.Holding(
            asset_id=ppf_asset.id,
            ticker_symbol=ppf_asset.ticker_symbol,
            asset_name=ppf_asset.name,
            asset_type=ppf_asset.asset_type,
            currency=ppf_asset.currency,
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
            account_number=ppf_asset.account_number,
            opening_date=opening_date,
        )

    # Separate transactions by type
    contributions = [
        t for t in transactions if t.transaction_type == TransactionType.CONTRIBUTION
    ]
    interest_credits = defaultdict(Decimal)
    for t in transactions:
        if t.transaction_type == TransactionType.INTEREST_CREDIT:
            fy_end_date = get_financial_year(t.transaction_date.date())[1]
            interest_credits[fy_end_date] += t.quantity

    balance = Decimal("0.0")
    total_investment = sum(t.quantity for t in contributions)
    total_credited_interest = Decimal("0.0")
    on_the_fly_interest = Decimal("0.0")

    # Iterate through financial years from opening date
    current_fy_start, _ = get_financial_year(opening_date)
    today = date.today()

    while current_fy_start <= today:
        fy_start, fy_end = get_financial_year(current_fy_start)

        transactions_in_fy = [
            t for t in contributions if fy_start <= t.transaction_date.date() <= fy_end
        ]

        if fy_end < today:  # Completed financial year
            if fy_end in interest_credits:
                interest_for_fy = interest_credits[fy_end]
            else:
                # Calculate and create missing interest transaction
                interest_for_fy = _calculate_ppf_interest_for_fy(
                    db, fy_start, fy_end, balance, transactions_in_fy
                )
                if interest_for_fy > 0:
                    # Check for existing credit before inserting (race condition protection)
                    existing_credit = db.query(Transaction).filter(
                        Transaction.asset_id == ppf_asset.id,
                        Transaction.transaction_type == TransactionType.INTEREST_CREDIT,
                        Transaction.transaction_date >= fy_end,
                        Transaction.transaction_date < fy_end + timedelta(days=1),
                    ).first()
                    
                    if not existing_credit:
                        try:
                            crud.transaction.create_with_portfolio(
                                db,
                                portfolio_id=portfolio_id,
                                obj_in=schemas.TransactionCreate(
                                    asset_id=ppf_asset.id,
                                    transaction_type=TransactionType.INTEREST_CREDIT,
                                    quantity=interest_for_fy,
                                    price_per_unit=1,
                                    transaction_date=fy_end.isoformat(),
                                ),
                            )
                            # Commit immediately to prevent duplicates from concurrent calls
                            db.commit()
                        except Exception:
                            # Another concurrent call may have inserted - rollback and check
                            db.rollback()
                            existing_credit = db.query(Transaction).filter(
                                Transaction.asset_id == ppf_asset.id,
                                Transaction.transaction_type == TransactionType.INTEREST_CREDIT,
                                Transaction.transaction_date >= fy_end,
                                Transaction.transaction_date < fy_end + timedelta(days=1),
                            ).first()
                            if existing_credit:
                                interest_for_fy = existing_credit.quantity
                    else:
                        interest_for_fy = existing_credit.quantity
            total_credited_interest += interest_for_fy
            balance += (
                sum(
                    t.quantity
                    for t in transactions_in_fy
                    if t.transaction_type == TransactionType.CONTRIBUTION
                )
                + interest_for_fy
            )
        else:  # Current, ongoing financial year
            on_the_fly_interest = _calculate_ppf_interest_for_fy(
                db, fy_start, fy_end, balance, transactions_in_fy
            )
            balance += (
                sum(
                    t.quantity
                    for t in transactions_in_fy
                    if t.transaction_type == TransactionType.CONTRIBUTION
                )
                + on_the_fly_interest
            )

        current_fy_start += relativedelta(years=1)

    # Clean up any duplicate interest credits created by concurrent calls
    _cleanup_duplicate_interest_credits(db, ppf_asset.id)

    total_interest_earned = total_credited_interest + on_the_fly_interest
    unrealized_pnl_percentage = (
        (total_interest_earned / total_investment) * 100
        if total_investment > 0
        else Decimal(0)
    )
    current_rate_obj = crud.historical_interest_rate.get_rate_for_date(
        db, scheme_name="PPF", a_date=date.today()
    )
    current_interest_rate = current_rate_obj.rate if current_rate_obj else None

    return schemas.Holding(
        asset_id=ppf_asset.id,
        ticker_symbol=ppf_asset.ticker_symbol,
        asset_name=ppf_asset.name,
        asset_type=ppf_asset.asset_type,
        currency=ppf_asset.currency,
        quantity=Decimal(1),
        average_buy_price=total_investment,
        current_price=balance,
        current_value=balance,
        total_invested_amount=total_investment,
        unrealized_pnl=on_the_fly_interest,
        realized_pnl=total_credited_interest,
        unrealized_pnl_percentage=float(unrealized_pnl_percentage),
        days_pnl=Decimal(0),
        days_pnl_percentage=0.0,
        group="GOVERNMENT_SCHEMES",
        account_number=ppf_asset.account_number,
        opening_date=opening_date,
        interest_rate=current_interest_rate,
    )


def trigger_ppf_recalculation(db: Session, asset_id: uuid.UUID) -> None:
    """Deletes future interest credits to trigger recalculation."""
    asset = crud.asset.get(db, id=asset_id)
    if not asset or asset.asset_type != AssetType.PPF:
        return

    logger.info(
        f"Triggering PPF recalculation for asset {asset_id}."
    )

    # This function is called when a contribution is modified.
    # We need to find the financial year of the change and delete all
    # system-generated interest credits from that year onwards.
    # For simplicity in this trigger, we will delete ALL interest credits
    # for the asset. The valuation logic is optimized to only recalculate
    # what's missing, so this is safe and effective.

    transactions_to_delete = db.query(Transaction).filter( # type: ignore
        Transaction.asset_id == asset_id,
        Transaction.transaction_type == TransactionType.INTEREST_CREDIT,
    ).all()

    if transactions_to_delete:
        logger.info(
            f"PPF Recalculation: Deleting {len(transactions_to_delete)} old "
            f"interest credit transactions for asset {asset_id}."
        )
        for t in transactions_to_delete:
            db.delete(t)
        db.flush()

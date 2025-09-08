from datetime import date
from decimal import Decimal
from typing import List

from app.schemas.transaction import TransactionCreate
from app.models.transaction import Transaction
from app.models.asset import Asset
from app.crud.crud_historical_interest_rate import historical_interest_rate
from sqlalchemy.orm import Session


def get_ppf_interest_rate(db: Session, for_date: date) -> Decimal:
    rate_record = historical_interest_rate.get_by_scheme_and_start_date(
        db, scheme_name="PPF", start_date=for_date
    )
    if rate_record:
        return rate_record.rate

    # If no exact match, find the rate for the period
    rate_record = (
        db.query(historical_interest_rate.model)
        .filter(
            historical_interest_rate.model.scheme_name == "PPF",
            historical_interest_rate.model.start_date <= for_date,
            historical_interest_rate.model.end_date >= for_date,
        )
        .first()
    )
    return rate_record.rate if rate_record else Decimal("0.0")


def calculate_ppf_interest(
    db: Session, asset: Asset, transactions: List[Transaction]
) -> List[TransactionCreate]:
    """
    Calculates the interest for a PPF account.
    """
    if not asset.opening_date:
        return []

    interest_transactions = []

    fy_start_year = asset.opening_date.year
    if asset.opening_date.month < 4:
        fy_start_year -= 1

    current_fy_start = date(fy_start_year, 4, 1)
    balance = Decimal("0.0")

    while current_fy_start.year < date.today().year:
        fy_end = date(current_fy_start.year + 1, 3, 31)

        fy_contributions = sum(
            tx.price_per_unit
            for tx in transactions
            if tx.transaction_type == "CONTRIBUTION"
            and current_fy_start <= tx.transaction_date.date() <= fy_end
        )

        interest_rate = get_ppf_interest_rate(db, for_date=fy_end) / 100
        interest_for_year = (balance + fy_contributions) * interest_rate

        if interest_for_year > 0:
            interest_transactions.append(
                TransactionCreate(
                    asset_id=asset.id,
                    transaction_type="INTEREST_CREDIT",
                    quantity=1,
                    price_per_unit=interest_for_year,
                    transaction_date=fy_end,
                    fees=0,
                )
            )

        balance += fy_contributions + interest_for_year
        current_fy_start = date(current_fy_start.year + 1, 4, 1)

    return interest_transactions

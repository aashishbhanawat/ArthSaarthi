from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Any

from app import crud, schemas
from app.models.transaction import Transaction
from app.tests.utils.asset import create_test_asset


def create_test_transaction(
    db: Session,
    *,
    portfolio_id: int,
    ticker: str,
    quantity: float,
    price_per_unit: float = 100.0,
    asset_type: str = "Stock",
    transaction_type: str = "buy",
    transaction_date: Optional[date] = None,
    fees: float = 0.0,
) -> Transaction:
    """
    Test utility to create a transaction.
    It will create the associated asset if it doesn't exist.
    """
    final_date = transaction_date or date.today()
    final_datetime = datetime.combine(final_date, datetime.min.time())

    asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker)
    if not asset:
        asset = create_test_asset(db, ticker_symbol=ticker)

    transaction_in = schemas.TransactionCreate(
        asset_id=asset.id,
        quantity=Decimal(str(quantity)),
        price_per_unit=Decimal(str(price_per_unit)),
        transaction_date=final_datetime,
        transaction_type=transaction_type.upper(),
        fees=Decimal(str(fees)),
    )
    return crud.transaction.create_with_portfolio(db=db, obj_in=transaction_in, portfolio_id=portfolio_id)
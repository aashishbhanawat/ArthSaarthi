from typing import Optional
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app import crud, schemas


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
) -> None:
    """
    Test utility to create a transaction.
    It will create the associated asset if it doesn't exist.
    """
    final_date = transaction_date or date.today()
    final_datetime = datetime.combine(final_date, datetime.min.time())

    asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker)
    if not asset:
        asset_in = schemas.AssetCreate(
            ticker_symbol=ticker, asset_type=asset_type, name=f"{ticker} Asset", currency="USD", exchange="NASDAQ"
        )
        asset = crud.asset.create(db, obj_in=asset_in)

    transaction_in = schemas.TransactionCreate(
        asset_id=asset.id,
        quantity=Decimal(str(quantity)),
        price_per_unit=Decimal(str(price_per_unit)),
        transaction_date=final_datetime,
        transaction_type=transaction_type.upper(),
    )
    crud.transaction.create_with_portfolio(db, obj_in=transaction_in, portfolio_id=portfolio_id)
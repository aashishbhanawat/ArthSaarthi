from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app import crud, schemas

def create_test_transaction(
    db: Session,
    *,
    portfolio_id: int,
    ticker: str,
    quantity: float,
    asset_type: str,
    price: float = 100.0,
    transaction_type: str = "buy",
    transaction_date: Optional[date] = None,
) -> None:
    """
    Test utility to create a transaction.
    It will create the associated asset if it doesn't exist by passing
    the new_asset schema to the CRUD layer, which mirrors the API flow.
    """
    # Use today's date if not provided, and convert to datetime for the schema
    final_date = transaction_date or date.today()
    final_datetime = datetime.combine(final_date, datetime.min.time())

    # Check if asset exists to decide whether to pass asset_id or new_asset
    asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker)

    transaction_in: schemas.TransactionCreate
    if asset:
        transaction_in = schemas.TransactionCreate(
            asset_id=asset.id,
            quantity=Decimal(str(quantity)),
            price_per_unit=Decimal(str(price)),
            transaction_date=final_datetime,
            transaction_type=transaction_type,
        )
    else:
        new_asset_in = schemas.AssetCreate(
            ticker_symbol=ticker,
            asset_type=asset_type,
            name=f"{ticker} Asset",
            currency="USD",
            exchange="NASDAQ",  # Provide a default exchange
        )
        transaction_in = schemas.TransactionCreate(
            new_asset=new_asset_in,
            quantity=Decimal(str(quantity)),
            price_per_unit=Decimal(str(price)),
            transaction_date=final_datetime,
            transaction_type=transaction_type,
        )

    crud.transaction.create_with_portfolio(
        db, obj_in=transaction_in, portfolio_id=portfolio_id
    )
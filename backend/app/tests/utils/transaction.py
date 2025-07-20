from sqlalchemy.orm import Session
from datetime import datetime

from app import crud, schemas
from app.models.asset import Asset

def create_test_transaction(
    db: Session,
    *,
    portfolio_id: int,
    ticker: str,
    quantity: float,
    asset_type: str,
    price: float = 100.0,
    transaction_type: str = "buy",
    transaction_date: datetime = None,
) -> None:
    """
    Test utility to create a transaction.
    It will also create the associated asset if it doesn't exist.
    """
    if transaction_date is None:
        transaction_date = datetime.utcnow()

    asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker)
    if not asset:
        asset_in = schemas.AssetCreate(
            ticker_symbol=ticker, asset_type=asset_type, name=f"{ticker} Asset", currency="USD"
        )
        asset = crud.asset.create(db, obj_in=asset_in)

    transaction_in = schemas.TransactionCreate(
        asset_id=asset.id,
        quantity=quantity,
        price_per_unit=price,
        fees=0.0,
        transaction_date=transaction_date,
        transaction_type=transaction_type,
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=transaction_in, portfolio_id=portfolio_id
    )
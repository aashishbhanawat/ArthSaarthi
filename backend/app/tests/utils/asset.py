from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.asset import Asset


def create_test_asset(db: Session, ticker_symbol: str) -> Asset:
    """
    Create a test asset in the database.
    """
    asset_in = schemas.AssetCreate(
        name=f"{ticker_symbol} Company",
        ticker_symbol=ticker_symbol,
        asset_type="STOCK",
        currency="USD",
        exchange="NASDAQ",
        isin=f"US-ISIN-{ticker_symbol}",
    )
    return crud.asset.create(db=db, obj_in=asset_in)
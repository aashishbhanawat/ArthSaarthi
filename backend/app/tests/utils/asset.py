from typing import Optional
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.asset import Asset


def create_test_asset(db: Session, *, ticker_symbol: str, name: Optional[str] = None) -> Asset:
    """
    Test utility to create an asset.
    """
    asset_name = name or f"{ticker_symbol} Company"
    asset_in = schemas.AssetCreate(
        name=asset_name,
        ticker_symbol=ticker_symbol,
        asset_type="STOCK",
        currency="USD",
        exchange="NASDAQ",
    )
    return crud.asset.create(db=db, obj_in=asset_in)
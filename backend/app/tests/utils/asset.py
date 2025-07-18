from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.asset import Asset


def create_test_asset(db: Session, ticker_symbol: str, name: str, asset_type: str = "STOCK", currency: str = "USD") -> Asset:
    asset_in = schemas.AssetCreate(
        ticker_symbol=ticker_symbol,
        name=name,
        asset_type=asset_type,
        currency=currency
    )
    return crud.asset.create(db=db, obj_in=asset_in)
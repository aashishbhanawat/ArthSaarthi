import random
import string
from typing import Optional

from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.asset import Asset


def random_string(length: int = 10) -> str:
    return "".join(random.choices(string.ascii_uppercase, k=length))


def create_random_asset(db: Session) -> Asset:
    ticker = random_string(4)
    return create_test_asset(db, ticker_symbol=ticker)


def create_test_asset(
    db: Session, *, ticker_symbol: str, name: Optional[str] = None
) -> Asset:
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

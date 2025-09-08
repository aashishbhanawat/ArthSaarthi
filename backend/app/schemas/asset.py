import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .enums import AssetType


# Properties to receive on asset creation via API
# This is a special schema for the POST /assets/ endpoint
class AssetCreateIn(BaseModel):
    ticker_symbol: str
    asset_type: Optional[AssetType] = None


# Properties to receive on asset creation (internal)
class AssetCreate(BaseModel):
    ticker_symbol: str
    name: str
    asset_type: AssetType
    currency: str | None = None
    exchange: str | None = None
    isin: str | None = None
    account_number: Optional[str] = None
    opening_date: Optional[date] = None


# Properties to receive on asset update
class AssetUpdate(BaseModel):
    name: str | None = None
    asset_type: str | None = None
    currency: str | None = None
    exchange: str | None = None


# Properties shared by models stored in DB
class AssetInDBBase(AssetCreate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Asset(AssetInDBBase):
    current_price: float | None = None
    day_change: float | None = None


# Properties to return from asset search
class AssetSearchResult(BaseModel):
    ticker_symbol: str
    name: str
    asset_type: str

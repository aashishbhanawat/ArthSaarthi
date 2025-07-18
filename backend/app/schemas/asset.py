from pydantic import BaseModel
from typing import Optional


# Shared properties
class AssetBase(BaseModel):
    ticker_symbol: str
    name: str
    asset_type: str
    currency: str


# Properties to receive on asset creation
class AssetCreate(AssetBase):
    pass


# Properties to receive on asset update
class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    currency: Optional[str] = None


# Properties shared by models stored in DB
class AssetInDBBase(AssetBase):
    id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Asset(AssetInDBBase):
    pass


# Properties stored in DB
class AssetInDB(AssetInDBBase):
    pass
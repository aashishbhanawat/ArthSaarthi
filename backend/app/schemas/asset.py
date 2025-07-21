from pydantic import BaseModel, ConfigDict
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

# Properties to return to client
class Asset(AssetBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Properties to receive on asset update
class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    currency: Optional[str] = None
from pydantic import BaseModel, ConfigDict
import uuid

# Properties to receive on asset creation via API
# This is a special schema for the POST /assets/ endpoint
class AssetCreateIn(BaseModel):
    ticker_symbol: str

# Properties to receive on asset creation (internal)
class AssetCreate(BaseModel):
    ticker_symbol: str
    name: str
    asset_type: str
    currency: str | None = None
    exchange: str | None = None

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
    pass
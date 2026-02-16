import uuid
from typing import Optional

from pydantic import BaseModel


class AssetAliasBase(BaseModel):
    alias_symbol: str
    source: str

class AssetAliasCreate(AssetAliasBase):
    asset_id: uuid.UUID

class AssetAliasUpdate(BaseModel):
    alias_symbol: Optional[str] = None
    source: Optional[str] = None
    asset_id: Optional[uuid.UUID] = None

class AssetAlias(AssetAliasBase):
    id: uuid.UUID
    asset_id: uuid.UUID

    class Config:
        from_attributes = True

class AssetAliasWithAsset(AssetAlias):
    """Alias response enriched with asset name and ticker for display."""
    asset_name: str = ""
    asset_ticker: str = ""

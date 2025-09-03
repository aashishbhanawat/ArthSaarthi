import uuid

from pydantic import BaseModel


class AssetAliasBase(BaseModel):
    alias_symbol: str
    source: str


class AssetAliasCreate(AssetAliasBase):
    asset_id: uuid.UUID


class AssetAlias(AssetAliasBase):
    id: uuid.UUID
    asset_id: uuid.UUID

    class Config:
        from_attributes = True

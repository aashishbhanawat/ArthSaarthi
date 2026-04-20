import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel

from .asset import Asset


# Schemas for WatchlistItem
# Properties shared by all WatchlistItem schemas
class WatchlistItemBase(BaseModel):
    asset_id: uuid.UUID


# Properties to receive via API on creation
class WatchlistItemCreate(WatchlistItemBase):
    pass


# Properties to receive via API on update
class WatchlistItemUpdate(WatchlistItemBase):
    pass


# Properties to return to client
class WatchlistItem(WatchlistItemBase):
    id: uuid.UUID
    watchlist_id: uuid.UUID
    user_id: uuid.UUID
    asset: Asset

    class Config:
        from_attributes = True
        orm_mode = True


# Schemas for Watchlist
# Shared properties
class WatchlistBase(BaseModel):
    name: str


# Properties to receive via API on creation
class WatchlistCreate(WatchlistBase):
    pass


# Properties to receive via API on update
class WatchlistUpdate(WatchlistBase):
    pass


# Properties to return to client
class Watchlist(WatchlistBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    items: List[WatchlistItem] = []

    class Config:
        from_attributes = True
        orm_mode = True

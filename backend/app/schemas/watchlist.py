import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


# Schemas for WatchlistItem
# Properties shared by all WatchlistItem schemas
class WatchlistItemBase(BaseModel):
    asset_id: uuid.UUID


# Properties to receive via API on creation
class WatchlistItemCreate(WatchlistItemBase):
    pass


# Properties to return to client
class WatchlistItem(WatchlistItemBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)

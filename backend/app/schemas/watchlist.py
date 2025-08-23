import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# Shared properties
class WatchlistBase(BaseModel):
    name: str


# Properties to receive on watchlist creation
class WatchlistCreate(WatchlistBase):
    pass


# Properties to receive on watchlist update
class WatchlistUpdate(BaseModel):
    name: Optional[str] = None


# Properties to return to client
class Watchlist(WatchlistBase):
    id: uuid.UUID
    user_id: uuid.UUID
    items: List = []
    model_config = ConfigDict(from_attributes=True)


class WatchlistItemBase(BaseModel):
    asset_id: uuid.UUID


class WatchlistItemCreate(WatchlistItemBase):
    pass


class WatchlistItem(WatchlistItemBase):
    id: uuid.UUID
    watchlist_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# Shared properties
class WatchlistBase(BaseModel):
    """Base schema for a watchlist, containing shared properties."""
    name: str


# Properties to receive on watchlist creation
class WatchlistCreate(WatchlistBase):
    """Schema for creating a new watchlist."""
    pass


# Properties to receive on watchlist update
class WatchlistUpdate(BaseModel):
    """Schema for updating an existing watchlist."""
    name: Optional[str] = None


# Properties to return to client
class Watchlist(WatchlistBase):
    """Schema for returning a watchlist to the client."""
    id: uuid.UUID
    user_id: uuid.UUID
    items: List = []
    model_config = ConfigDict(from_attributes=True)


class WatchlistItemBase(BaseModel):
    """Base schema for a watchlist item."""
    asset_id: uuid.UUID


class WatchlistItemCreate(WatchlistItemBase):
    """Schema for creating a new watchlist item."""
    pass


class WatchlistItem(WatchlistItemBase):
    """Schema for returning a watchlist item to the client."""
    id: uuid.UUID
    watchlist_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

import uuid
from typing import List

from pydantic import BaseModel

from .asset import Asset


class WatchlistItemBase(BaseModel):
    asset_id: uuid.UUID

class WatchlistItemCreate(WatchlistItemBase):
    pass

class WatchlistItem(WatchlistItemBase):
    id: uuid.UUID
    watchlist_id: uuid.UUID
    asset: Asset

    class Config:
        orm_mode = True

class WatchlistBase(BaseModel):
    name: str

class WatchlistCreate(WatchlistBase):
    pass

class WatchlistUpdate(WatchlistBase):
    pass

class Watchlist(WatchlistBase):
    id: uuid.UUID
    user_id: uuid.UUID
    items: List[WatchlistItem] = []

    class Config:
        orm_mode = True

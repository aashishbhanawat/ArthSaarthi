import uuid
from typing import List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistItemCreate,
    WatchlistUpdate,
)


class CRUDWatchlist(CRUDBase[Watchlist, WatchlistCreate, WatchlistUpdate]):
    """CRUD operations for watchlists."""

    def create_with_owner(
        self, db: Session, *, obj_in: WatchlistCreate, user_id: uuid.UUID
    ) -> Watchlist:
        """Create a new watchlist for a specific user."""
        db_obj = Watchlist(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Watchlist]:
        """Get all watchlists for a specific user."""
        return (
            db.query(self.model)
            .filter(Watchlist.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


class CRUDWatchlistItem(CRUDBase[WatchlistItem, WatchlistItemCreate, WatchlistUpdate]):
    """CRUD operations for watchlist items."""

    def create_with_owner(
        self,
        db: Session,
        *,
        obj_in: WatchlistItemCreate,
        watchlist_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> WatchlistItem:
        """Create a new watchlist item for a specific user and watchlist."""
        db_obj = WatchlistItem(
            **obj_in.model_dump(), watchlist_id=watchlist_id, user_id=user_id
        )
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj


watchlist = CRUDWatchlist(Watchlist)
watchlist_item = CRUDWatchlistItem(WatchlistItem)

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.watchlist import Watchlist, WatchlistItem
from ..schemas.watchlist import WatchlistCreate, WatchlistUpdate
from .base import CRUDBase


class CRUDWatchlist(CRUDBase[Watchlist, WatchlistCreate, WatchlistUpdate]):
    def get_by_user(self, db: Session, *, user_id: uuid.UUID) -> List[Watchlist]:
        return db.query(self.model).filter(self.model.user_id == user_id).all()

    def create_with_user(
        self, db: Session, *, obj_in: WatchlistCreate, user_id: uuid.UUID
    ) -> Watchlist:
        db_obj = self.model(**obj_in.dict(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def add_item(
        self, db: Session, *, watchlist_id: uuid.UUID, asset_id: uuid.UUID
    ) -> WatchlistItem:
        db_obj = WatchlistItem(watchlist_id=watchlist_id, asset_id=asset_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove_item(
        self, db: Session, *, watchlist_id: uuid.UUID, item_id: uuid.UUID
    ) -> Optional[WatchlistItem]:
        item = (
            db.query(WatchlistItem)
            .filter(
                WatchlistItem.id == item_id,
                WatchlistItem.watchlist_id == watchlist_id,
            )
            .first()
        )
        if item:
            db.delete(item)
            db.commit()
        return item


watchlist = CRUDWatchlist(Watchlist)

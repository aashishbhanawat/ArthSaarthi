import uuid

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.watchlist import WatchlistItem
from app.schemas.watchlist import WatchlistItemCreate


class CRUDWatchlistItem(
    CRUDBase[WatchlistItem, WatchlistItemCreate, WatchlistItemCreate]
):
    def create_with_watchlist_and_user(
        self,
        db: Session,
        *,
        obj_in: WatchlistItemCreate,
        watchlist_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WatchlistItem:
        db_obj = WatchlistItem(
            **obj_in.model_dump(),
            watchlist_id=watchlist_id,
            user_id=user_id,
        )
        db.add(db_obj)
        return db_obj


watchlist_item = CRUDWatchlistItem(WatchlistItem)

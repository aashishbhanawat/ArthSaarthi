from typing import List
import uuid

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.watchlist import Watchlist
from app.schemas.watchlist import WatchlistCreate, WatchlistUpdate


class CRUDWatchlist(CRUDBase[Watchlist, WatchlistCreate, WatchlistUpdate]):
    def create_with_user(
        self, db: Session, *, obj_in: WatchlistCreate, user_id: uuid.UUID
    ) -> Watchlist:
        db_obj = Watchlist(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.flush()
        return db_obj

    def get_multi_by_user(
        self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Watchlist]:
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


watchlist = CRUDWatchlist(Watchlist)

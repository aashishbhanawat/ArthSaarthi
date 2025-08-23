from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.watchlist import WatchlistCreate
from app.tests.utils.user import create_random_user


def create_random_watchlist(db: Session, *, user_id: str = None) -> models.Watchlist:
    if user_id is None:
        user = create_random_user(db)
        user_id = user.id
    watchlist_in = WatchlistCreate(name="Test Watchlist")
    return crud.watchlist.create_with_owner(db=db, obj_in=watchlist_in, user_id=user_id)

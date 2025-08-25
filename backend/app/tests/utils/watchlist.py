import random
import string
import uuid

from sqlalchemy.orm import Session

from app import crud
from app.models.watchlist import Watchlist
from app.schemas.watchlist import WatchlistCreate


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def create_random_watchlist(db: Session, *, user_id: uuid.UUID) -> Watchlist:
    watchlist_name = random_lower_string()
    watchlist_in = WatchlistCreate(name=watchlist_name)
    return crud.watchlist.create_with_user(db=db, obj_in=watchlist_in, user_id=user_id)

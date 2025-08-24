import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User as UserModel
from app.schemas.watchlist import Watchlist, WatchlistCreate, WatchlistUpdate

router = APIRouter()


@router.get("/", response_model=List[Watchlist])
def read_watchlists(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Retrieve all watchlists for the current user.
    """
    watchlists = crud.watchlist.get_multi_by_user(db, user_id=current_user.id)
    return watchlists


@router.post("/", response_model=Watchlist, status_code=status.HTTP_201_CREATED)
def create_watchlist(
    *,
    db: Session = Depends(get_db),
    watchlist_in: WatchlistCreate,
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Create new watchlist.
    """
    watchlist = crud.watchlist.create_with_user(
        db, obj_in=watchlist_in, user_id=current_user.id
    )
    db.commit()
    return watchlist


@router.get("/{watchlist_id}", response_model=Watchlist)
def read_watchlist(
    *,
    db: Session = Depends(get_db),
    watchlist_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get watchlist by ID.
    """
    watchlist = crud.watchlist.get(db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if watchlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return watchlist


@router.put("/{watchlist_id}", response_model=Watchlist)
def update_watchlist(
    *,
    db: Session = Depends(get_db),
    watchlist_id: uuid.UUID,
    watchlist_in: WatchlistUpdate,
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Update a watchlist.
    """
    watchlist = crud.watchlist.get(db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if watchlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    watchlist = crud.watchlist.update(db, db_obj=watchlist, obj_in=watchlist_in)
    db.commit()
    db.refresh(watchlist)
    return watchlist


@router.delete("/{watchlist_id}", response_model=Watchlist)
def delete_watchlist(
    *,
    db: Session = Depends(get_db),
    watchlist_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Delete a watchlist.
    """
    watchlist = crud.watchlist.get(db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if watchlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    watchlist = crud.watchlist.remove(db, id=watchlist_id)
    db.commit()
    return watchlist

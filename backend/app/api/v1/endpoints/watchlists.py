import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .... import crud, models, schemas
from ....core.dependencies import get_current_active_user, get_db

router = APIRouter()


@router.get("/", response_model=List[schemas.Watchlist])
def read_watchlists(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve user's watchlists.
    """
    watchlists = crud.watchlist.get_by_user(db, user_id=current_user.id)
    return watchlists


@router.post("/", response_model=schemas.Watchlist)
def create_watchlist(
    *,
    db: Session = Depends(get_db),
    watchlist_in: schemas.WatchlistCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Create new watchlist.
    """
    watchlist = crud.watchlist.create_with_user(
        db, obj_in=watchlist_in, user_id=current_user.id
    )
    return watchlist


@router.put("/{id}", response_model=schemas.Watchlist)
def update_watchlist(
    *,
    db: Session = Depends(get_db),
    id: uuid.UUID,
    watchlist_in: schemas.WatchlistUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Update a watchlist.
    """
    watchlist = crud.watchlist.get(db, id=id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if watchlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    watchlist = crud.watchlist.update(db, db_obj=watchlist, obj_in=watchlist_in)
    return watchlist


@router.delete("/{id}", response_model=schemas.Watchlist)
def delete_watchlist(
    *,
    db: Session = Depends(get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a watchlist.
    """
    watchlist = crud.watchlist.get(db, id=id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if watchlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    watchlist = crud.watchlist.remove(db, id=id)
    return watchlist


@router.post("/{watchlist_id}/items", response_model=schemas.WatchlistItem)
def add_watchlist_item(
    *,
    db: Session = Depends(get_db),
    watchlist_id: uuid.UUID,
    item_in: schemas.WatchlistItemCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Add an item to a watchlist.
    """
    watchlist = crud.watchlist.get(db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if watchlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    item = crud.watchlist.add_item(
        db, watchlist_id=watchlist_id, asset_id=item_in.asset_id
    )
    return item


@router.delete("/{watchlist_id}/items/{item_id}", response_model=schemas.WatchlistItem)
def delete_watchlist_item(
    *,
    db: Session = Depends(get_db),
    watchlist_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Delete an item from a watchlist.
    """
    watchlist = crud.watchlist.get(db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if watchlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    item = crud.watchlist.remove_item(db, watchlist_id=watchlist_id, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return item

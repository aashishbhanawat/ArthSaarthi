import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core import dependencies
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[schemas.Watchlist])
def read_watchlists(
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Retrieve watchlists for the current user.
    """
    watchlists = crud.watchlist.get_multi_by_owner(db=db, user_id=current_user.id)
    return watchlists


@router.post("/", response_model=schemas.Watchlist, status_code=201)
def create_watchlist(
    *,
    db: Session = Depends(dependencies.get_db),
    watchlist_in: schemas.WatchlistCreate,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create new watchlist.
    """
    watchlist = crud.watchlist.create_with_owner(
        db=db, obj_in=watchlist_in, user_id=current_user.id
    )
    db.commit()
    return watchlist


@router.get("/{watchlist_id}", response_model=schemas.Watchlist)
def read_watchlist(
    *,
    db: Session = Depends(dependencies.get_db),
    watchlist_id: uuid.UUID,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get watchlist by ID.
    """
    watchlist = crud.watchlist.get(db=db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if not current_user.is_admin and (watchlist.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return watchlist


@router.put("/{watchlist_id}", response_model=schemas.Watchlist)
def update_watchlist(
    *,
    db: Session = Depends(dependencies.get_db),
    watchlist_id: uuid.UUID,
    watchlist_in: schemas.WatchlistUpdate,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Update a watchlist.
    """
    watchlist = crud.watchlist.get(db=db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if not current_user.is_admin and (watchlist.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    watchlist = crud.watchlist.update(db=db, db_obj=watchlist, obj_in=watchlist_in)
    db.commit()
    return watchlist


@router.delete("/{watchlist_id}", response_model=schemas.Msg)
def delete_watchlist(
    *,
    db: Session = Depends(dependencies.get_db),
    watchlist_id: uuid.UUID,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a watchlist.
    """
    watchlist = crud.watchlist.get(db=db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if not current_user.is_admin and (watchlist.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    crud.watchlist.remove(db=db, id=watchlist_id)
    db.commit()
    return {"msg": "Watchlist deleted successfully"}


@router.post(
    "/{watchlist_id}/items",
    response_model=schemas.WatchlistItem,
    status_code=201,
)
def add_watchlist_item(
    *,
    db: Session = Depends(dependencies.get_db),
    watchlist_id: uuid.UUID,
    item_in: schemas.WatchlistItemCreate,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Add an item to a watchlist.
    """
    watchlist = crud.watchlist.get(db=db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if not current_user.is_admin and (watchlist.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    item = crud.watchlist_item.create_with_owner(
        db=db, obj_in=item_in, watchlist_id=watchlist_id, user_id=current_user.id
    )
    db.commit()
    return item


@router.delete("/{watchlist_id}/items/{item_id}", response_model=schemas.Msg)
def remove_watchlist_item(
    *,
    db: Session = Depends(dependencies.get_db),
    watchlist_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Remove an item from a watchlist.
    """
    watchlist = crud.watchlist.get(db=db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if not current_user.is_admin and (watchlist.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    item = crud.watchlist_item.get(db=db, id=item_id)
    if not item or item.watchlist_id != watchlist_id:
        raise HTTPException(status_code=404, detail="Item not found in this watchlist")
    crud.watchlist_item.remove(db=db, id=item_id)
    db.commit()
    return {"msg": "Item removed successfully"}

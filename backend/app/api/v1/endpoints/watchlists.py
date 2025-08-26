import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app import crud
from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User as UserModel
from app.models.watchlist import Watchlist as WatchlistModel
from app.models.watchlist import WatchlistItem as WatchlistItemModel
from app.schemas.watchlist import (
    Watchlist,
    WatchlistCreate,
    WatchlistItem,
    WatchlistItemCreate,
    WatchlistUpdate,
)
from app.services.financial_data_service import financial_data_service

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
    Get watchlist by ID, with its items and asset details.
    """
    watchlist = (
        db.query(WatchlistModel)
        .options(joinedload(WatchlistModel.items).joinedload(WatchlistItemModel.asset))
        .filter(WatchlistModel.id == watchlist_id)
        .first()
    )

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if watchlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Enrich with live data
    if watchlist.items:
        assets_to_fetch = [
            {"ticker_symbol": item.asset.ticker_symbol, "exchange": item.asset.exchange}
            for item in watchlist.items
        ]
        price_data = financial_data_service.get_current_prices(assets_to_fetch)
        for item in watchlist.items:
            data = price_data.get(item.asset.ticker_symbol)
            if data:
                item.asset.current_price = data.get("current_price")
                item.asset.day_change = (
                    data["current_price"] - data["previous_close"]
                    if "current_price" in data and "previous_close" in data
                    else None
                )

    return watchlist


@router.post(
    "/{watchlist_id}/items",
    response_model=WatchlistItem,
    status_code=status.HTTP_201_CREATED,
)
def add_watchlist_item(
    *,
    db: Session = Depends(get_db),
    watchlist_id: uuid.UUID,
    item_in: WatchlistItemCreate,
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Add an item to a watchlist.
    """
    watchlist = crud.watchlist.get(db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if watchlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Check if asset exists
    asset = crud.asset.get(db, id=item_in.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Check if item already exists
    # This should be handled by the DB unique constraint, but a 400 is nicer.
    for item in watchlist.items:
        if item.asset_id == item_in.asset_id:
            raise HTTPException(
                status_code=400, detail="Asset already in this watchlist"
            )

    watchlist_item = crud.watchlist_item.create_with_watchlist_and_user(
        db, obj_in=item_in, watchlist_id=watchlist_id, user_id=current_user.id
    )
    db.commit()
    db.refresh(watchlist_item)
    return watchlist_item


@router.delete("/{watchlist_id}/items/{item_id}", response_model=WatchlistItem)
def remove_watchlist_item(
    *,
    db: Session = Depends(get_db),
    watchlist_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Remove an item from a watchlist.
    """
    watchlist = crud.watchlist.get(db, id=watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if watchlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    item = crud.watchlist_item.get(db, id=item_id)
    if not item or item.watchlist_id != watchlist_id:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    deleted_item = crud.watchlist_item.remove(db, id=item_id)
    db.commit()
    return deleted_item


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
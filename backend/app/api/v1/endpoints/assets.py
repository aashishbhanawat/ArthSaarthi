import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import dependencies as deps
from app.core.config import settings
from app.models.user import User
from app.services.financial_data_service import financial_data_service

router = APIRouter()


@router.post("/", response_model=schemas.Asset, status_code=status.HTTP_201_CREATED)
def create_asset(
    *,
    db: Session = Depends(deps.get_db),
    asset_in: schemas.AssetCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new asset.
    """
    if settings.DEBUG:
        print("--- CREATE ASSET ENDPOINT HIT ---")
        print(f"User: {current_user.email}, Payload: {asset_in.model_dump_json()}")
    asset = crud.asset.get_by_ticker(db, ticker_symbol=asset_in.ticker_symbol)
    if asset:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An asset with this ticker symbol already exists in the system.",
        )
    new_asset = crud.asset.create(db=db, obj_in=asset_in)
    db.commit()
    db.refresh(new_asset)
    return new_asset


@router.get("/", response_model=List[schemas.Asset])
def read_assets(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Retrieve all assets.
    """
    assets = crud.asset.get_multi(db, skip=skip, limit=limit)
    return assets


@router.get("/lookup/", response_model=List[schemas.Asset])
def lookup_ticker_symbol(
    query: str = Query(..., min_length=2, max_length=50),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Search for an asset by its ticker symbol or name from the local database.
    The database is expected to be seeded with a master list of assets.
    """
    assets = crud.asset.search_by_name_or_ticker(db, query=query)
    if settings.DEBUG:
        print("--- BACKEND DEBUG: Asset Lookup ---")
        print(f"Received query: '{query}'")
        print(f"Found {len(assets)} assets.")
        print("---------------------------------")
    if assets:
        return assets
    return []


@router.get("/search-mf/", response_model=List[schemas.AssetSearchResult])
def search_mutual_funds(
    *,
    query: str = Query(..., min_length=3, max_length=50),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Search for Indian Mutual Funds by name or scheme code from the AMFI data source.
    """
    # The financial_data_service singleton handles caching.
    results = financial_data_service.search_mutual_funds(query=query)
    if not results:
        return []
    return results


@router.get("/{asset_id}", response_model=schemas.Asset)
def read_asset(
    asset_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get a specific asset by its ID.
    """
    asset = crud.asset.get(db, id=str(asset_id))
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

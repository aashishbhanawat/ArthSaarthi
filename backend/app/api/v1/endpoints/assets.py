import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core import dependencies as deps
from app.core.config import settings
from app.models.user import User
from app.services.financial_data_service import financial_data_service

router = APIRouter()


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
    query: str = Query(..., min_length=3, max_length=50, alias="q"),
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

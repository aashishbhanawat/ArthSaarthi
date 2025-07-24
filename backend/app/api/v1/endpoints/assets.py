from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core import dependencies as deps
from app.services.financial_data_service import financial_data_service
from app.models.user import User

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
def read_asset_by_id(
    asset_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get a specific asset by its ID.
    """
    asset = crud.asset.get(db, id=asset_id)
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
    Search for an asset by its ticker symbol or name.
    It first checks the local database. If not found, it queries the external financial data service.
    If found externally, the asset is created in the local database.
    """
    # 1. Search in the local database first
    assets = crud.asset.search_by_name_or_ticker(db, query=query)
    if assets:
        return assets

    # 2. If not found locally, try the external financial service
    try:
        details = financial_data_service.get_asset_details(ticker=query)
        if not details:
            return []

        # 3. If found externally, create it in our local database
        # Ensure ticker_symbol is in the details for schema validation
        details["ticker_symbol"] = query
        asset_in = schemas.AssetCreate(**details)
        new_asset = crud.asset.create(db=db, obj_in=asset_in)
        return [new_asset]

    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Financial data service is unavailable: {e}"
        )

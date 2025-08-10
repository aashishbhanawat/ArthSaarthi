import uuid
from typing import List

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


@router.post("/", response_model=schemas.Asset, status_code=201)
def create_asset(
    *,
    db: Session = Depends(deps.get_db),
    asset_in: schemas.AssetCreateIn,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create a new asset in the system after validating it against an external service.
    This is used when a user wants to add a transaction for an asset not yet in the DB.
    The request body only needs the ticker_symbol.
    """
    ticker = asset_in.ticker_symbol.upper()
    db_asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker)
    if db_asset:
        raise HTTPException(
            status_code=409,
            detail="An asset with this ticker symbol already exists.",
        )

    details = financial_data_service.get_asset_details(ticker)
    if not details:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Could not find a valid asset with ticker symbol '{ticker}' on"
                " supported exchanges."
            ),
        )

    new_asset_data = schemas.AssetCreate(ticker_symbol=ticker, **details)

    asset = crud.asset.create(db=db, obj_in=new_asset_data)
    db.commit()
    return asset

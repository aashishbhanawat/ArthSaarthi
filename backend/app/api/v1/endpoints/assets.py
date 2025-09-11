import uuid
from datetime import date
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


@router.get("/check-ppf", response_model=schemas.Asset)
def check_ppf_account(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Check if a PPF account exists for the current user.
    """
    ppf_asset = crud.asset.get_by_type_and_user(
        db=db, asset_type="PPF", user_id=current_user.id
    )
    if not ppf_asset:
        raise HTTPException(status_code=404, detail="PPF account not found")
    return ppf_asset


@router.post("/create-ppf-with-contribution", status_code=status.HTTP_201_CREATED)
def create_ppf_with_contribution(
    *,
    db: Session = Depends(deps.get_db),
    ppf_in: schemas.PpfAccountCreateWithContribution,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new PPF account and its first contribution.
    """
    # This is a simplified approach. A more robust solution would be to
    # create this logic in a dedicated CRUD function.

    # 1. Create the Asset
    asset_in = schemas.AssetCreate(
        name=ppf_in.institutionName,
        ticker_symbol=f"PPF-{ppf_in.accountNumber or date.today()}",
        asset_type="PPF",
        currency="INR",
        account_number=ppf_in.accountNumber,
        opening_date=ppf_in.openingDate,
    )
    asset = crud.asset.create_with_owner(
        db=db, obj_in=asset_in, owner_id=current_user.id
    )

    # 2. Create the first contribution
    # We need a portfolio to associate the transaction with.
    # The portfolioId is now passed in the request.
    portfolio = crud.portfolio.get(db=db, id=ppf_in.portfolioId)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )

    transaction_in = schemas.TransactionCreate(
        asset_id=asset.id,
        transaction_type="CONTRIBUTION",
        quantity=ppf_in.contributionAmount,
        price_per_unit=1,
        transaction_date=ppf_in.contributionDate,
    )
    crud.transaction.create_with_portfolio(
        db=db, obj_in=transaction_in, portfolio_id=ppf_in.portfolioId
    )

    db.commit()
    return {"msg": "PPF Account and first contribution created successfully"}


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

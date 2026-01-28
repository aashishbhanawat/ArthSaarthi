import uuid
from typing import Any, List, Optional

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
    # --- START OF DEBUG LOGS ---
    if settings.DEBUG:
        print("\n--- BACKEND DEBUG: CREATE ASSET ENDPOINT HIT ---")
        print(f"User: {current_user.email}")
        print(f"Received Payload: {asset_in.model_dump_json(indent=2)}")

    asset = crud.asset.get_by_ticker(db, ticker_symbol=asset_in.ticker_symbol)

    if settings.DEBUG:
        if asset:
            print(f"Asset with ticker '{asset_in.ticker_symbol}' "
                  f"already exists in DB. ID: {asset.id}")
        else:
            print(f"Asset with ticker '{asset_in.ticker_symbol}' "
                  f"does NOT exist in DB. Proceeding with creation.")
        print("-------------------------------------------------\n")
    # --- END OF DEBUG LOGS ---
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


@router.get("/search-stocks/", response_model=List[schemas.AssetSearchResult])
def search_stocks(
    query: str = Query(..., min_length=2, max_length=50),
    asset_type: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Search for stocks/assets without creating them. Returns search results
    from both local database and Yahoo Finance. Use this endpoint for
    autocomplete/typeahead. Asset is only created when user selects via /lookup/.
    """
    results = []

    # 1. Search local database first
    local_assets = crud.asset.search_by_name_or_ticker(
        db, query=query, asset_type=asset_type
    )
    for asset in local_assets:
        results.append({
            "id": str(asset.id),  # Include id for local assets
            "ticker_symbol": asset.ticker_symbol,
            "name": asset.name,
            "asset_type": asset.asset_type,
            "exchange": asset.exchange,
            "currency": asset.currency,
            "source": "local",
            "fmv_2018": float(asset.fmv_2018) if asset.fmv_2018 else None,
        })

    # 2. If few local results, also search Yahoo Finance
    if len(results) < 5:
        search_results = financial_data_service.search_stocks(query)
        for r in search_results:
            ticker = r.get("ticker_symbol", "")

            # Skip Indian exchange tickers (already in local DB via NSDL sync)
            if ticker.upper().endswith('.NS') or ticker.upper().endswith('.BO'):
                continue

            # Skip if already in local results
            if any(
                lr["ticker_symbol"] == ticker
                for lr in results
            ):
                continue

            # Filter by asset_type if provided
            if asset_type and r.get("asset_type", "").upper() != asset_type.upper():
                continue

            results.append({
                "ticker_symbol": ticker,
                "name": r.get("name"),
                "asset_type": r.get("asset_type", "STOCK"),
                "exchange": r.get("exchange"),
                "currency": r.get("currency"),
                "source": "yahoo",
            })

    if settings.DEBUG:
        print(f"Search for '{query}' returned {len(results)} results")

    return results[:15]  # Limit total results


@router.get("/lookup/", response_model=List[schemas.Asset])
def lookup_ticker_symbol(
    query: str = Query(..., min_length=2, max_length=50),
    asset_type: Optional[str] = None,
    force_external: bool = Query(
        False, description="Skip local search and force external lookup"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Search for an asset by its ticker symbol or name.
    It first searches the local database. If not found, it queries the
    external financial data service. If found there, it creates the asset
    locally and returns it.

    Set force_external=true to skip local search and create from external source
    (used when user selects a Yahoo result from search).
    """
    # 1. Search local database (unless force_external)
    if not force_external:
        assets = crud.asset.search_by_name_or_ticker(
            db, query=query, asset_type=asset_type
        )
        if assets:
            if settings.DEBUG:
                print("--- BACKEND DEBUG: Asset Lookup ---")
                print(f"Found {len(assets)} assets locally for query: '{query}'")
                print("---------------------------------")
            return assets

    # If asset_type is BOND and no local assets were found, do not query external
    # service.
    if asset_type == "BOND":
        if settings.DEBUG:
            print("--- BACKEND DEBUG: Asset Lookup ---")
            print(f"No local BOND asset found for '{query}'. "
                  "External lookup is disabled for bonds.")
            print("---------------------------------")
        return []

    # 2. If not found locally, query external service (case-insensitive for ticker)
    if settings.DEBUG:
        print("--- BACKEND DEBUG: Asset Lookup ---")
        print(f"No local asset found for '{query}'. Querying external service...")
        print("---------------------------------")

    # 2a. First, try direct ticker lookup (for exact ticker matches like "LEN")
    resolved_ticker = query.upper().strip()  # Default to cleaned query
    details = financial_data_service.get_asset_details(ticker_symbol=resolved_ticker)

    # 2b. If direct lookup fails and query contains spaces or is a company name,
    # use Yahoo search to find the ticker
    if not details:
        if settings.DEBUG:
            print(f"Direct lookup failed. Trying Yahoo search for '{query}'...")

        search_results = financial_data_service.search_stocks(query)
        if search_results:
            # Filter by asset_type if provided
            if asset_type:
                search_results = [
                    r for r in search_results
                    if r.get("asset_type", "").upper() == asset_type.upper()
                ]

            if search_results:
                # Try to get details for the first matching result
                ticker = search_results[0].get("ticker_symbol")
                if ticker:
                    if settings.DEBUG:
                        print(f"Yahoo search found ticker: {ticker}")
                    details = financial_data_service.get_asset_details(
                        ticker_symbol=ticker
                    )
                    if details:
                        resolved_ticker = ticker  # Use the ticker from search

    if not details:
        if settings.DEBUG:
            print("--- BACKEND DEBUG: Asset Lookup ---")
            print(f"No asset found in external service for '{query.upper()}'.")
            print("---------------------------------")
        return []

    # 2a. If an asset_type filter was provided, ensure the external result matches.
    if asset_type and details.get("asset_type", "").upper() != asset_type.upper():
        if settings.DEBUG:
            print("--- BACKEND DEBUG: Asset Lookup ---")
            print(f"External asset found, but type '{details.get('asset_type')}' "
                  f"does not match requested type '{asset_type}'. Discarding.")
            print("---------------------------------")
        return []

    # 2a. If an asset_type filter was provided, ensure the external result matches.
    if asset_type and details.get("asset_type", "").upper() != asset_type.upper():
        if settings.DEBUG:
            print("--- BACKEND DEBUG: Asset Lookup ---")
            print(f"External asset found, but type '{details.get('asset_type')}' "
                  f"does not match requested type '{asset_type}'. Discarding.")
            print("---------------------------------")
        return []

    # 3. If found externally, create it locally
    # Use the resolved ticker (from search or cleaned query)
    details["ticker_symbol"] = resolved_ticker
    details["asset_type"] = details["asset_type"].upper()

    # Check if asset already exists by ticker (may have been created by
    # concurrent request or restore)
    ticker = details["ticker_symbol"]
    existing_asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker)
    if existing_asset:
        if settings.DEBUG:
            print("--- BACKEND DEBUG: Asset Lookup ---")
            print(f"Asset '{ticker}' already exists. Returning.")
            print("---------------------------------")
        return [existing_asset]

    # Also check by name+type+currency to avoid duplicate key errors.
    # This handles cases where the same asset has different tickers
    # on different exchanges.
    existing_by_name = db.query(models.Asset).filter(
        models.Asset.name == details.get("name"),
        models.Asset.asset_type == details.get("asset_type"),
        models.Asset.currency == details.get("currency")
    ).first()
    if existing_by_name:
        if settings.DEBUG:
            print("--- BACKEND DEBUG: Asset Lookup ---")
            print(
                f"Asset with same name/type/currency exists: "
                f"{existing_by_name.ticker_symbol}"
            )
            print("---------------------------------")
        return [existing_by_name]

    asset_in = schemas.AssetCreate(**details)
    new_asset = crud.asset.create(db=db, obj_in=asset_in)
    db.commit()
    db.refresh(new_asset)

    if settings.DEBUG:
        print("--- BACKEND DEBUG: Asset Lookup ---")
        print(f"Created new asset from external service: {new_asset.name}")
        print("---------------------------------")

    return [new_asset]


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

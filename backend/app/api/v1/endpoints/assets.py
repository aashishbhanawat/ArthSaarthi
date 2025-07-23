from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core import dependencies as deps
from app.models.user import User
from app.services.financial_data_service import financial_data_service

router = APIRouter()


@router.get("/lookup/{ticker_symbol}", response_model=schemas.Asset)
def lookup_ticker_symbol(
    ticker_symbol: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Lookup an asset by its ticker symbol.
    1. Check local DB.
    2. If not found, check external service.
    3. If found externally, create it in local DB and return it.
    4. If not found anywhere, return 404.
    """
    asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker_symbol)
    if asset:
        return asset

    try:
        details = financial_data_service.get_asset_details(ticker_symbol)
        if details:
            details["ticker_symbol"] = ticker_symbol
            asset_in = schemas.AssetCreate(**details)
            return crud.asset.create(db=db, obj_in=asset_in)
    except Exception:
        raise HTTPException(status_code=503, detail="Error communicating with financial data service")

    raise HTTPException(status_code=404, detail="Ticker symbol not found")

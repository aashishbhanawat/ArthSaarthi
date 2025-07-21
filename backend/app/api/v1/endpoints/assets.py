from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models import user as user_model
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.core.config import settings
from app.services.financial_data_service import FinancialDataService

router = APIRouter()


@router.get("/lookup/{ticker_symbol}", response_model=schemas.Asset)
def lookup_ticker_symbol(
    ticker_symbol: str,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
) -> Any:
    """
    Look up an asset. First in the local DB, then from the external service.
    """
    # 1. Check local database first (case-insensitive)
    asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker_symbol.upper())
    if asset:
        return asset

    # 2. If not found, check the external service
    try:
        financial_data_service = FinancialDataService(
            api_key=settings.FINANCIAL_API_KEY, api_url=settings.FINANCIAL_API_URL
        )
        asset_details = financial_data_service.get_asset_details(ticker_symbol)
        if asset_details:
            asset_details["id"] = -1  # Sentinel ID for assets not yet in our DB
            asset_details["ticker_symbol"] = ticker_symbol.upper()
            return schemas.Asset(**asset_details)
    except Exception:
        pass  # Fall through to the final error if external service fails

    # 3. If not found in either place, raise 404
    raise HTTPException(status_code=404, detail="Ticker symbol not found in external service")
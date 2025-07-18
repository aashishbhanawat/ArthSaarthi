from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.services.financial_data_service import FinancialDataService
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter()


def get_financial_data_service():
    return FinancialDataService(api_key=settings.FINANCIAL_API_KEY, api_url=settings.FINANCIAL_API_URL)


@router.get("/lookup/{ticker_symbol}")
async def lookup_ticker_symbol(
    ticker_symbol: str,
    current_user: User = Depends(get_current_user),
    financial_service: FinancialDataService = Depends(get_financial_data_service),
):
    """
    Look up asset details from the external financial API.
    """
    return await financial_service.lookup_ticker(ticker_symbol)
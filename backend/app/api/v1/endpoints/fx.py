from datetime import date
from decimal import Decimal
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core import dependencies
from app.models.user import User
from app.services.financial_data_service import financial_data_service

router = APIRouter()


@router.get("/", response_model=Dict[str, Decimal])
def get_fx_rate(
    from_currency: str = Query(..., alias="from", min_length=3, max_length=3),
    to_currency: str = Query(..., alias="to", min_length=3, max_length=3),
    date_obj: date = Query(..., alias="date"),
    current_user: User = Depends(dependencies.get_current_user),
) -> Dict[str, Decimal]:
    """
    Get exchange rate between two currencies for a specific date.
    """
    rate = financial_data_service.get_exchange_rate(from_currency.upper(), to_currency.upper(), date_obj)
    if rate is None:
        raise HTTPException(status_code=404, detail="Exchange rate not found")

    return {"rate": rate}

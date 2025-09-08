import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models
from app.core.dependencies import get_current_admin_user, get_db
from app.schemas.historical_interest_rate import (
    HistoricalInterestRate,
    HistoricalInterestRateCreate,
    HistoricalInterestRateUpdate,
)

router = APIRouter()


@router.post(
    "/interest-rates/",
    response_model=HistoricalInterestRate,
    status_code=201,
)
def create_historical_interest_rate(
    *,
    db: Session = Depends(get_db),
    rate_in: HistoricalInterestRateCreate,
    current_user: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    Create a new historical interest rate. (Admin only)
    """
    rate = crud.historical_interest_rate.get_by_scheme_and_start_date(
        db, scheme_name=rate_in.scheme_name, start_date=rate_in.start_date
    )
    if rate:
        raise HTTPException(
            status_code=400,
            detail="An interest rate for this scheme and start date already exists.",
        )
    return crud.historical_interest_rate.create(db, obj_in=rate_in)


@router.get(
    "/interest-rates/",
    response_model=List[HistoricalInterestRate],
)
def read_historical_interest_rates(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    Retrieve historical interest rates. (Admin only)
    """
    return crud.historical_interest_rate.get_multi(db, skip=skip, limit=limit)


@router.put(
    "/interest-rates/{rate_id}",
    response_model=HistoricalInterestRate,
)
def update_historical_interest_rate(
    *,
    db: Session = Depends(get_db),
    rate_id: uuid.UUID,
    rate_in: HistoricalInterestRateUpdate,
    current_user: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    Update a historical interest rate. (Admin only)
    """
    rate = crud.historical_interest_rate.get(db, id=rate_id)
    if not rate:
        raise HTTPException(status_code=404, detail="Interest rate not found")
    return crud.historical_interest_rate.update(db, db_obj=rate, obj_in=rate_in)


@router.delete(
    "/interest-rates/{rate_id}",
    response_model=HistoricalInterestRate,
)
def delete_historical_interest_rate(
    *,
    db: Session = Depends(get_db),
    rate_id: uuid.UUID,
    current_user: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    Delete a historical interest rate. (Admin only)
    """
    rate = crud.historical_interest_rate.get(db, id=rate_id)
    if not rate:
        raise HTTPException(status_code=404, detail="Interest rate not found")
    return crud.historical_interest_rate.remove(db, id=rate_id)

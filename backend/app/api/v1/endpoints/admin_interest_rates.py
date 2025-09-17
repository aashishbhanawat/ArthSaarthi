import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.dependencies import get_current_admin_user
from app.db.session import get_db
from app.models.user import User as UserModel

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.HistoricalInterestRate],
    tags=["admin-interest-rates"],
)
def read_historical_interest_rates(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """
    Retrieve a list of all historical interest rates. (Admin Only)
    """
    rates = crud.historical_interest_rate.get_multi(db)
    return rates


@router.post(
    "/",
    response_model=schemas.HistoricalInterestRate,
    status_code=status.HTTP_201_CREATED,
    tags=["admin-interest-rates"],
)
def create_historical_interest_rate(
    rate_in: schemas.HistoricalInterestRateCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """
    Create a new historical interest rate. (Admin Only)
    """
    rate = crud.historical_interest_rate.create(db, obj_in=rate_in)
    db.commit()
    db.refresh(rate)
    return rate


@router.put(
    "/{rate_id}",
    response_model=schemas.HistoricalInterestRate,
    tags=["admin-interest-rates"],
)
def update_historical_interest_rate(
    rate_id: uuid.UUID,
    rate_in: schemas.HistoricalInterestRateUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """
    Update an existing historical interest rate. (Admin Only)
    """
    rate = crud.historical_interest_rate.get(db, id=rate_id)
    if not rate:
        raise HTTPException(status_code=404, detail="Interest rate not found")
    updated_rate = crud.historical_interest_rate.update(db, db_obj=rate, obj_in=rate_in)
    db.commit()
    db.refresh(updated_rate)
    return updated_rate


@router.delete(
    "/{rate_id}",
    response_model=schemas.HistoricalInterestRate,
    tags=["admin-interest-rates"],
)
def delete_historical_interest_rate(
    rate_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
) -> Any:
    """
    Delete a historical interest rate. Returns the deleted object.
    """
    rate = crud.historical_interest_rate.get(db, id=rate_id)
    if not rate:
        raise HTTPException(status_code=404, detail="Interest rate not found")
    crud.historical_interest_rate.remove(db, id=rate_id)
    db.commit()
    return rate

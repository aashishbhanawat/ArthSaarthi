import uuid
from datetime import date
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.dependencies import get_current_admin_user
from app.db.session import get_db
from app.models.asset import Asset as AssetModel
from app.models.user import User as UserModel

router = APIRouter()


def _trigger_ppf_recalculation(db: Session, from_date: date):
    """
    Finds all PPF assets and deletes their interest credits from a given date.
    This forces a recalculation on the next portfolio valuation.
    """
    ppf_assets = db.query(AssetModel).filter(AssetModel.asset_type == "PPF").all()
    for asset in ppf_assets:
        crud.transaction.remove_interest_credits_from_date(
            db=db, asset_id=asset.id, from_date=from_date
        )
    # The commit is handled by the calling function to maintain transactional integrity.



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

    _trigger_ppf_recalculation(db, from_date=rate.start_date)
    db.commit()  # Commit the transaction deletions

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
    db_rate = crud.historical_interest_rate.get(db, id=rate_id)
    if not db_rate:
        raise HTTPException(status_code=404, detail="Interest rate not found")

    # Determine if a recalculation is needed
    recalculation_needed = (
        rate_in.rate is not None
        or rate_in.start_date is not None
        or rate_in.end_date is not None
    )

    updated_rate = crud.historical_interest_rate.update(
        db, db_obj=db_rate, obj_in=rate_in
    )

    if recalculation_needed:
        # This is a "heavy" operation but ensures data consistency.
        # A more advanced implementation might use a background job queue.
        recalc_start_date = rate_in.start_date or db_rate.start_date
        _trigger_ppf_recalculation(db, from_date=recalc_start_date)

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

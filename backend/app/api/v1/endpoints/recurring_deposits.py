import uuid
from typing import Any

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import dependencies
from app.crud.crud_holding import _calculate_rd_value_at_date

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.recurring_deposit.RecurringDeposit,
    status_code=status.HTTP_201_CREATED,
)
def create_recurring_deposit(
    *,
    db: Session = Depends(dependencies.get_db),
    rd_in: schemas.RecurringDepositCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create new recurring deposit.
    """
    portfolio = crud.portfolio.get(db=db, id=rd_in.portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Portfolio not found or not owned by user"
        )

    rd = crud.recurring_deposit.create_with_portfolio(
        db=db, obj_in=rd_in, user_id=current_user.id
    )
    db.commit()
    db.refresh(rd)
    return rd


@router.get("/{id}", response_model=schemas.recurring_deposit.RecurringDepositDetails)
def read_recurring_deposit(
    *,
    db: Session = Depends(dependencies.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get recurring deposit by ID.
    """
    rd = crud.recurring_deposit.get(db=db, id=id)
    if not rd:
        raise HTTPException(status_code=404, detail="Recurring Deposit not found")
    if not current_user.is_admin and (rd.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    maturity_date = rd.start_date + relativedelta(months=rd.tenure_months)
    maturity_value = _calculate_rd_value_at_date(
        monthly_installment=rd.monthly_installment,
        interest_rate=rd.interest_rate,
        start_date=rd.start_date,
        tenure_months=rd.tenure_months,
        calculation_date=maturity_date,
    )

    return schemas.recurring_deposit.RecurringDepositDetails(
        **schemas.recurring_deposit.RecurringDeposit.model_validate(rd).model_dump(),
        maturity_value=maturity_value,
    )


@router.get(
    "/{id}/analytics",
    response_model=schemas.recurring_deposit.RecurringDepositAnalytics,
)
def get_recurring_deposit_analytics(
    *,
    db: Session = Depends(dependencies.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get recurring deposit analytics by ID.
    """
    rd = crud.recurring_deposit.get(db=db, id=id)
    if not rd:
        raise HTTPException(status_code=404, detail="Recurring Deposit not found")
    if not current_user.is_admin and (rd.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return crud.analytics.get_recurring_deposit_analytics(db=db, rd=rd)


@router.put("/{id}", response_model=schemas.recurring_deposit.RecurringDeposit)
def update_recurring_deposit(
    *,
    db: Session = Depends(dependencies.get_db),
    id: uuid.UUID,
    rd_in: schemas.recurring_deposit.RecurringDepositUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Update a recurring deposit.
    """
    rd = crud.recurring_deposit.get(db=db, id=id)
    if not rd:
        raise HTTPException(status_code=404, detail="Recurring deposit not found")
    if not current_user.is_admin and (rd.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    rd = crud.recurring_deposit.update(db=db, db_obj=rd, obj_in=rd_in)
    db.commit()
    db.refresh(rd)
    return rd


@router.delete("/{id}", response_model=schemas.Msg)
def delete_recurring_deposit(
    *,
    db: Session = Depends(dependencies.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a recurring deposit.
    """
    rd = crud.recurring_deposit.get(db=db, id=id)
    if not rd:
        raise HTTPException(status_code=404, detail="Recurring Deposit not found")
    if not current_user.is_admin and (rd.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    crud.recurring_deposit.remove(db=db, id=id)
    db.commit()
    return {"msg": "Recurring deposit deleted successfully."}

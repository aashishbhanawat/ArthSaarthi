import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.cache.utils import invalidate_caches_for_portfolio
from app.core import dependencies
from app.crud.crud_holding import _calculate_fd_current_value

router = APIRouter()


@router.post(
    "/", response_model=schemas.FixedDeposit, status_code=status.HTTP_201_CREATED
)
def create_fixed_deposit(
    *,
    db: Session = Depends(dependencies.get_db),
    fd_in: schemas.FixedDepositCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create new fixed deposit.
    """
    portfolio = crud.portfolio.get(db=db, id=fd_in.portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Portfolio not found or not owned by user"
        )

    fd = crud.fixed_deposit.create_with_portfolio(
        db=db, obj_in=fd_in, user_id=current_user.id
    )
    invalidate_caches_for_portfolio(db=db, portfolio_id=portfolio.id)
    db.commit()
    db.refresh(fd)
    return fd


@router.get("/{fd_id}", response_model=schemas.fixed_deposit.FixedDepositDetails)
def read_fixed_deposit(
    *,
    db: Session = Depends(dependencies.get_db),
    fd_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get fixed deposit by ID, including calculated maturity value.
    """
    fd = crud.fixed_deposit.get(db=db, id=fd_id)
    if not fd:
        raise HTTPException(status_code=404, detail="Fixed Deposit not found")
    if not current_user.is_admin and (fd.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    maturity_value = _calculate_fd_current_value(
        principal=fd.principal_amount,
        interest_rate=fd.interest_rate,
        start_date=fd.start_date,
        end_date=fd.maturity_date,
        compounding_frequency=fd.compounding_frequency,
        interest_payout=fd.interest_payout,
    )
    response_data = schemas.FixedDeposit.model_validate(fd).model_dump()
    response_data["maturity_value"] = maturity_value
    return response_data


@router.get("/{fd_id}/analytics", response_model=schemas.FixedDepositAnalytics)
def get_fd_analytics(
    *,
    db: Session = Depends(dependencies.get_db),
    fd_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get advanced analytics for a specific fixed deposit.
    """
    fd = crud.fixed_deposit.get(db=db, id=fd_id)
    if not fd:
        raise HTTPException(status_code=404, detail="Fixed Deposit not found")
    if not current_user.is_admin and (fd.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    analytics = crud.analytics.get_fixed_deposit_analytics(db=db, fd=fd)
    return analytics


@router.put("/{fd_id}", response_model=schemas.FixedDeposit)
def update_fixed_deposit(
    *,
    db: Session = Depends(dependencies.get_db),
    fd_id: uuid.UUID,
    fd_in: schemas.FixedDepositUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Update a fixed deposit.
    """
    fd = crud.fixed_deposit.get(db=db, id=fd_id)
    if not fd:
        raise HTTPException(status_code=404, detail="Fixed deposit not found")
    if not current_user.is_admin and (fd.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    fd = crud.fixed_deposit.update(db=db, db_obj=fd, obj_in=fd_in)
    invalidate_caches_for_portfolio(db=db, portfolio_id=fd.portfolio_id)
    db.commit()
    db.refresh(fd)
    return fd

@router.delete("/{fd_id}", response_model=schemas.Msg)
def delete_fixed_deposit(
    *,
    db: Session = Depends(dependencies.get_db),
    fd_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a fixed deposit.
    """
    fd = crud.fixed_deposit.get(db=db, id=fd_id)
    if not fd:
        raise HTTPException(status_code=404, detail="Fixed Deposit not found")
    if not current_user.is_admin and (fd.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    portfolio_id = fd.portfolio_id
    crud.fixed_deposit.remove(db=db, id=fd_id)
    invalidate_caches_for_portfolio(db=db, portfolio_id=portfolio_id)
    db.commit()
    return {"msg": "Fixed deposit deleted successfully"}

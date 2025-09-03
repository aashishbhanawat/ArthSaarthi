import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import dependencies as deps

router = APIRouter()


@router.post("/portfolios/{portfolio_id}/fixed-deposits", response_model=schemas.Asset)
def create_fixed_deposit(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: uuid.UUID,
    fixed_deposit_in: schemas.FixedDepositCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> models.Asset:
    """
    Create new fixed deposit for a portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    asset = crud.fixed_income.create_fixed_deposit(
        db=db, portfolio_id=portfolio_id, fixed_deposit_in=fixed_deposit_in
    )
    return asset


@router.post("/portfolios/{portfolio_id}/bonds", response_model=schemas.Asset)
def create_bond(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: uuid.UUID,
    bond_in: schemas.BondCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> models.Asset:
    """
    Create new bond for a portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    asset = crud.fixed_income.create_bond(
        db=db, portfolio_id=portfolio_id, bond_in=bond_in
    )
    return asset


@router.post("/portfolios/{portfolio_id}/ppf", response_model=schemas.Asset)
def create_ppf(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: uuid.UUID,
    ppf_in: schemas.PublicProvidentFundCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> models.Asset:
    """
    Create new PPF account for a portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    asset = crud.fixed_income.create_ppf(
        db=db, portfolio_id=portfolio_id, ppf_in=ppf_in
    )
    return asset

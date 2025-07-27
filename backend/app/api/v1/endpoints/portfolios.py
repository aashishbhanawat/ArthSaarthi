from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import dependencies
from app.models.user import User
from . import transactions

router = APIRouter()
router.include_router(transactions.router, prefix="/{portfolio_id}/transactions", tags=["transactions"])


@router.get("/", response_model=List[schemas.Portfolio])
def read_portfolios(
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Retrieve portfolios for the current user.
    """
    portfolios = crud.portfolio.get_multi_by_owner(
        db=db, user_id=current_user.id
    )
    return portfolios


@router.post("/", response_model=schemas.Portfolio, status_code=201)
def create_portfolio(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_in: schemas.PortfolioCreate,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create new portfolio.
    """
    portfolio = crud.portfolio.create_with_owner(
        db=db, obj_in=portfolio_in, user_id=current_user.id
    )
    return portfolio


@router.get("/{id}", response_model=schemas.Portfolio)
def read_portfolio(
    *,
    db: Session = Depends(dependencies.get_db),
    id: int,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get portfolio by ID.
    """
    portfolio = crud.portfolio.get(db=db, id=id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if not current_user.is_admin and (portfolio.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return portfolio


@router.delete("/{id}")
def delete_portfolio(
    *,
    db: Session = Depends(dependencies.get_db),
    id: int,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if not current_user.is_admin and (portfolio.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    crud.portfolio.remove(db=db, id=id)
    return {"message": "Portfolio deleted successfully"}
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core import dependencies as deps
from app.models.user import User
from . import transactions

router = APIRouter()


@router.post("/", response_model=schemas.Portfolio, status_code=201)
def create_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_in: schemas.PortfolioCreate,
    current_user: User = Depends(deps.get_current_user),
):
    portfolio = crud.portfolio.create_with_owner(
        db=db, obj_in=portfolio_in, user_id=current_user.id
    )
    return portfolio


@router.get("/", response_model=List[schemas.Portfolio])
def read_portfolios(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    portfolios = crud.portfolio.get_multi_by_owner(db=db, user_id=current_user.id)
    return portfolios


@router.get("/{portfolio_id}", response_model=schemas.Portfolio)
def read_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    current_user: User = Depends(deps.get_current_user),
):
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return portfolio


@router.delete("/{portfolio_id}")
def delete_portfolio(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    current_user: User = Depends(deps.get_current_user),
):
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    crud.portfolio.remove(db=db, id=portfolio_id)
    return {"message": "Portfolio deleted successfully"}


router.include_router(
    transactions.router, prefix="/{portfolio_id}/transactions", tags=["transactions"]
)
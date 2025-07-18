from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core import dependencies
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[schemas.Portfolio])
def read_portfolios(
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user),
):
    """
    Retrieve all portfolios for the current user.
    """
    return crud.portfolio.get_multi_by_owner(db=db, user_id=current_user.id)


@router.post("/", response_model=schemas.Portfolio, status_code=201)
def create_portfolio(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_in: schemas.PortfolioCreate,
    current_user: User = Depends(dependencies.get_current_user),
):
    """
    Create new portfolio.
    """
    return crud.portfolio.create_with_owner(db=db, obj_in=portfolio_in, user_id=current_user.id)


@router.get("/{portfolio_id}", response_model=schemas.Portfolio)
def read_portfolio(
    portfolio_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user),
):
    """
    Get a specific portfolio by id.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.delete("/{portfolio_id}", response_model=schemas.Msg)
def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user),
):
    """
    Delete a portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    crud.portfolio.remove(db=db, id=portfolio_id)
    return {"msg": "Portfolio deleted successfully"}
from typing import Any, List

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import settings
from app.core import dependencies
from app.models.user import User
from . import transactions
from app.crud import crud_analytics


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
    db.commit()
    if settings.DEBUG:
        print(f"--- BACKEND DEBUG: Portfolio Created ---")
        print(f"Portfolio Name: {portfolio.name}")
        print(f"Portfolio ID (UUID): {portfolio.id}")
        print(f"------------------------------------")
    return portfolio


@router.get("/{portfolio_id}", response_model=schemas.Portfolio)
def read_portfolio(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get portfolio by ID.
    """
    if settings.DEBUG:
        print(f"--- BACKEND DEBUG: Get Portfolio by ID ---")
        print(f"Received request for portfolio_id: {portfolio_id}")
        print(f"Type of portfolio_id: {type(portfolio_id)}")
        print(f"------------------------------------")
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if not current_user.is_admin and (portfolio.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return portfolio


@router.delete("/{portfolio_id}", response_model=schemas.Msg)
def delete_portfolio(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if not current_user.is_admin and (portfolio.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    crud.portfolio.remove(db=db, id=portfolio_id)    
    db.commit()
    return {"msg": "Portfolio deleted successfully"}

@router.get("/{portfolio_id}/analytics", response_model=schemas.AnalyticsResponse)
def get_portfolio_analytics(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get advanced analytics for a specific portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    analytics = crud_analytics.get_portfolio_analytics(db=db, portfolio_id=portfolio_id)
    return analytics


@router.get("/{portfolio_id}/summary", response_model=schemas.PortfolioSummary)
def get_portfolio_summary(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get summary metrics for a specific portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if not current_user.is_admin and (portfolio.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = crud.holding.get_portfolio_holdings_and_summary(db=db, portfolio_id=portfolio_id)
    return result["summary"]


@router.get("/{portfolio_id}/holdings", response_model=schemas.HoldingsResponse)
def get_portfolio_holdings(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get the consolidated holdings for a specific portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if not current_user.is_admin and (portfolio.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = crud.holding.get_portfolio_holdings_and_summary(db=db, portfolio_id=portfolio_id)
    return {"holdings": result["holdings"]}

@router.get("/{portfolio_id}/assets/{asset_id}/transactions", response_model=List[schemas.Transaction])
def read_asset_transactions(portfolio_id: uuid.UUID, asset_id: uuid.UUID, db: Session = Depends(dependencies.get_db), current_user: models.User = Depends(dependencies.get_current_user)):
    # Basic ownership check
    portfolio = crud.portfolio.get(db, id=portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return crud.transaction.get_multi_by_portfolio_and_asset(db, portfolio_id=portfolio_id, asset_id=asset_id)


@router.get("/{portfolio_id}/assets/{asset_id}/analytics", response_model=schemas.AssetAnalytics)
def get_asset_analytics(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    asset_id: uuid.UUID,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get advanced analytics for a specific asset in a portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return crud_analytics.get_asset_analytics(db=db, portfolio_id=portfolio_id, asset_id=asset_id)
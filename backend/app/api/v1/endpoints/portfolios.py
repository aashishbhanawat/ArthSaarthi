import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.cache.factory import get_cache_client
from app.core import dependencies
from app.services.benchmark_service import BenchmarkService
from app.services.financial_data_service import FinancialDataService

from . import bonds as bonds_router

router = APIRouter()


@router.get("/", response_model=List[schemas.Portfolio])
def read_portfolios(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """Retrieve portfolios for the current user."""
    return crud.portfolio.get_multi_by_owner(db=db, user_id=current_user.id)


@router.post("/", response_model=schemas.Portfolio, status_code=201)
def create_portfolio(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_in: schemas.PortfolioCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """Create new portfolio."""
    portfolio = crud.portfolio.create_with_owner(
        db=db, obj_in=portfolio_in, user_id=current_user.id
    )
    db.commit()
    return portfolio


@router.get("/{portfolio_id}", response_model=schemas.Portfolio)
def read_portfolio(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get portfolio by ID.
    """
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
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    crud.portfolio.remove(db=db, id=portfolio_id)
    db.commit()
    return {"msg": "Portfolio deleted successfully"}


@router.get("/{portfolio_id}/analytics", response_model=schemas.PortfolioAnalytics)
def get_portfolio_analytics(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get advanced analytics for a specific portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    analytics = crud.analytics.get_portfolio_analytics(db=db, portfolio_id=portfolio_id)
    return analytics


@router.get("/{portfolio_id}/summary", response_model=schemas.PortfolioSummary)
def get_portfolio_summary(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get summary metrics for a specific portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = crud.holding.get_portfolio_holdings_and_summary(
        db=db, portfolio_id=portfolio_id
    )
    return result.summary


@router.get("/{portfolio_id}/holdings", response_model=schemas.HoldingsResponse)
def get_portfolio_holdings(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get the consolidated holdings for a specific portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = crud.holding.get_portfolio_holdings_and_summary(
        db=db, portfolio_id=portfolio_id
    )
    return {"holdings": result.holdings}


@router.get("/{portfolio_id}/assets", response_model=List[schemas.Asset])
def get_portfolio_assets(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get all assets for a specific portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if not current_user.is_admin and (portfolio.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return crud.asset.get_multi_by_portfolio(db=db, portfolio_id=portfolio_id)


@router.get(
    "/{portfolio_id}/assets/{asset_id}/transactions",
    response_model=List[schemas.Transaction],
)
def read_asset_transactions(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    asset_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """Retrieve transactions for a specific asset within a portfolio."""
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if not current_user.is_admin and (portfolio.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return crud.transaction.get_multi_by_portfolio_and_asset(
        db, portfolio_id=portfolio_id, asset_id=asset_id
    )


@router.get(
    "/{portfolio_id}/assets/{asset_id}/analytics", response_model=schemas.AssetAnalytics
)
def get_asset_analytics(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    asset_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get advanced analytics for a specific asset in a portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return crud.analytics.get_asset_analytics(
        db=db, portfolio_id=portfolio_id, asset_id=asset_id
    )


@router.get(
    "/{portfolio_id}/diversification",
    response_model=schemas.DiversificationResponse
)
def get_portfolio_diversification(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get diversification analysis for a specific portfolio (FR6.4).
    Returns breakdown by asset class, sector, and geography.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return crud.analytics.get_diversification(db=db, portfolio_id=portfolio_id)

router.include_router(
    bonds_router.router,
    prefix="/{portfolio_id}/bonds",
    tags=["bonds"],
)



def get_benchmark_service(
    db: Session = Depends(dependencies.get_db),
) -> BenchmarkService:
    cache_client = get_cache_client()
    financial_service = FinancialDataService(cache_client=cache_client)
    return BenchmarkService(db=db, financial_service=financial_service)


@router.get("/{portfolio_id}/benchmark-comparison")
def get_benchmark_comparison(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    benchmark_ticker: str = "^NSEI",
    benchmark_mode: str = "single",
    hybrid_preset: str = None,
    risk_free_rate: float = 7.0,
    current_user: models.User = Depends(dependencies.get_current_user),
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
) -> Any:
    """
    Compare portfolio performance with a benchmark (hypothesis: invested in index).
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if not current_user.is_admin and (portfolio.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return benchmark_service.calculate_benchmark_performance(
        portfolio_id=str(portfolio_id),
        benchmark_ticker=benchmark_ticker,
        benchmark_mode=benchmark_mode,
        hybrid_preset=hybrid_preset,
        risk_free_rate=risk_free_rate
    )

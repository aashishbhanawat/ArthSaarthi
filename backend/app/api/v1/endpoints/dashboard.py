from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core import dependencies as deps
from app.models.user import User as UserModel

router = APIRouter()


class HistoryRange(str, Enum):
    d7 = "7d"
    d30 = "30d"
    y1 = "1y"
    all = "all"


@router.get("/summary", response_model=schemas.DashboardSummary)
def get_dashboard_summary(
    *,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_user),
):
    """
    Retrieve a summary of the user's dashboard data, including total value,
    asset allocation, and value per portfolio.
    """
    summary = crud.dashboard.get_summary(db=db, user=current_user)
    return summary


@router.get("/history", response_model=schemas.PortfolioHistoryResponse)
def get_portfolio_history(
    *,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_user),
    range: HistoryRange = Query(
        HistoryRange.d30, description="Time range for the history data"
    ),
):
    """
    Retrieve historical portfolio value data for a specified time range.
    """
    history = crud.dashboard.get_history(
        db=db, user=current_user, range_str=range.value
    )
    return {"history": history}


@router.get("/allocation", response_model=List[schemas.AssetAllocation])
def get_asset_allocation(
    *,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_user),
) -> List[schemas.AssetAllocation]:
    """
    Retrieve asset allocation for the current user.
    """
    allocation = crud.dashboard.get_allocation(db=db, user=current_user)
    return allocation

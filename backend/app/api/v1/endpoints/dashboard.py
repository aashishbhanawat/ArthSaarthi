from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.user import User
from app.core import dependencies

router = APIRouter()


@router.get("/summary", response_model=schemas.DashboardSummary)
def get_dashboard_summary(
    *,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user),
):
    """
    Retrieve a summary of the user's dashboard data, including total value,
    asset allocation, and value per portfolio.
    """
    return crud.dashboard.get_dashboard_summary(db=db, user=current_user)
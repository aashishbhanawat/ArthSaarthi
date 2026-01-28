"""
Schedule FA API Endpoint

Reports foreign assets for ITR-2/ITR-3 Schedule FA.
Uses CALENDAR YEAR (Jan-Dec) not Financial Year.
"""
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core import dependencies as deps
from app.models import User
from app.schemas.schedule_fa import ScheduleFAEntry, ScheduleFASummary
from app.services.schedule_fa_service import ScheduleFAService

router = APIRouter()


@router.get("/", response_model=ScheduleFASummary)
def get_schedule_fa(
    calendar_year: int = Query(..., description="Calendar Year (e.g., 2024)"),
    portfolio_id: Optional[str] = Query(None, description="Filter by Portfolio ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get Schedule FA (Foreign Assets) Report for a calendar year.
    
    Note: Schedule FA follows CALENDAR YEAR (Jan 1 - Dec 31),
    NOT Financial Year. For AY 2025-26, use calendar_year=2024.
    
    Returns:
    - List of foreign assets held during the year
    - Initial value (Jan 1), Peak value, Closing value (Dec 31)
    - Gross proceeds from sales
    """
    service = ScheduleFAService(db)
    entries_data = service.get_schedule_fa(
        user_id=str(current_user.id),
        calendar_year=calendar_year,
        portfolio_id=portfolio_id
    )

    # Convert to Pydantic models
    entries = [ScheduleFAEntry(**e) for e in entries_data]

    # Calculate totals
    total_initial = sum(e.initial_value for e in entries)
    total_peak = sum(e.peak_value for e in entries)
    total_closing = sum(e.closing_value for e in entries)
    total_proceeds = sum(e.gross_proceeds_from_sale for e in entries)

    # Determine assessment year
    assessment_year = f"{calendar_year + 1}-{str(calendar_year + 2)[-2:]}"

    return ScheduleFASummary(
        calendar_year=calendar_year,
        assessment_year=assessment_year,
        entries=entries,
        total_initial_value=total_initial,
        total_peak_value=total_peak,
        total_closing_value=total_closing,
        total_gross_proceeds=total_proceeds,
    )

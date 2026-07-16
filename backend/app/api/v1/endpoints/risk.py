from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import dependencies

router = APIRouter()


@router.get("/", response_model=schemas.UserRiskProfile)
def read_risk_profile(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Retrieve the current user's risk profile.
    """
    profile = crud.risk_profile.get_by_user(db=db, user_id=current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk profile not found. Please complete the questionnaire.",
        )
    return profile


@router.post("/", response_model=schemas.UserRiskProfile, status_code=201)
def create_or_update_risk_profile(
    *,
    db: Session = Depends(dependencies.get_db),
    profile_in: schemas.UserRiskProfileCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create or update the user's risk profile answers.
    """
    profile = crud.risk_profile.create_or_update(
        db=db, user_id=current_user.id, obj_in=profile_in
    )
    db.commit()
    db.refresh(profile)
    return profile

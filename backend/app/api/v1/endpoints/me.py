from fastapi import APIRouter, Depends

from app import models, schemas
from app.core.dependencies import get_current_user

router = APIRouter()


@router.get("/me", response_model=schemas.User)
def read_user_me(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Get current user."""
    return current_user

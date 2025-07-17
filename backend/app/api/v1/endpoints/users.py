from fastapi import APIRouter, Depends
import logging
from app.core.dependencies import get_current_user
from app.models.user import User as UserModel
from app.schemas.user import User as UserSchema

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """Get current user."""
    logger.info(f"Accessed /users/me by user: {current_user.email}")
    return current_user
from fastapi import APIRouter, Depends
 
from app.schemas import user as user_schema
from app.core.dependencies import get_current_user

router = APIRouter()


@router.get("/me", response_model=user_schema.User)
def read_users_me(current_user: user_schema.User = Depends(get_current_user)):
    """
    Get current user.
    """
    return current_user
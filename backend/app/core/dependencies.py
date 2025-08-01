from fastapi import Depends, HTTPException, status
import logging
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud import crud_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload
from app.core.config import settings
from app.core import security

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

logger = logging.getLogger(__name__)


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = security.decode_access_token(token)
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        logger.warning("Invalid token received", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = crud_user.user.get_user_by_email(db, email=token_data.sub)
    if not user:
        logger.warning(
            f"User not found for email in token: {token_data.sub}")
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not crud_user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """
    Dependency to check if the current user is an admin.
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.email} attempted to access admin-only endpoint.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin user"
        )
    return current_user

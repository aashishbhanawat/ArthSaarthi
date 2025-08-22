import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud
from app.core import security
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload

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
    try:
        user = crud.user.get_by_email(db, email=token_data.sub)
        if not user:
            logger.warning(f"User not found for email in token: {token_data.sub}")
            raise HTTPException(status_code=404, detail="User not found")
    except RuntimeError as e:
        # This can happen in desktop mode if the app is restarted and the key
        # manager is not yet unlocked by user login.
        if "master key is not loaded" in str(e):
            logger.warning("Could not get user by email, master key not loaded.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Master key not loaded, please log in again.",
            )
        # Re-raise other runtime errors
        raise
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """
    Dependency to check if the current user is an admin.
    """
    if not current_user.is_admin:
        logger.warning(
            "Non-admin user %s attempted to access admin-only endpoint.",
            current_user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin user"
        )
    return current_user

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
import logging
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
 
from app.models import user as user_model
from app.core import security
from app.core.config import settings
from app.crud import crud_user
from app.db.session import get_db
from app.core import dependencies as deps
from app.schemas.auth import Status
from app.schemas import token as token_schema
from app.schemas.user import User, UserCreate

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/status", response_model=Status)
def get_setup_status(db: Session = Depends(get_db)):
    """Check if the initial admin user has been created."""
    user_count = db.query(user_model.User).count()
    return {"setup_needed": user_count == 0}


@router.post("/setup", response_model=User)
def setup_admin_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create the first admin user. This will fail if any user already exists.
    """
    logger.info(f"Attempting to setup admin user: {user.email}")
    user_count = db.query(user_model.User).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin account already exists.",
        )
    db_user = crud_user.create_user(db=db, user=user, is_admin=True)
    return db_user


@router.post("/login", response_model=token_schema.Token)
def login(
    *,
    db: Session = Depends(get_db),
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    logger.info(f"Login attempt for user: {form_data.username}")
    user = crud_user.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(subject=user.id)
    refresh_token = security.create_refresh_token(subject=user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=token_schema.Token)
def refresh(
    *,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials, no refresh token found",
        )

    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        
        user_id = int(payload.get("sub"))
        user = crud_user.get_user(db, id=user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not find active user")

        access_token = security.create_access_token(subject=user.id)
        return {"access_token": access_token, "token_type": "bearer"}

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials, token is invalid or expired",
        )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}
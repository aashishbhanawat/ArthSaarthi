from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
import logging
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
 
from app.models import user as user_model
from app.core import security
from app.core.config import settings
from app.crud import crud_user
from app.db.session import get_db
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
def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    logger.info(f"Login attempt for user: {form_data.username}")
    user = crud_user.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
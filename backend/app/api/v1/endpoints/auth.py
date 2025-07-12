from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
 
from app.crud import crud_user
from app.schemas import user as user_schema, token as token_schema
from app.models import user as user_model
from app.core import security
from app.core.config import settings
from app.db.session import get_db

router = APIRouter()


@router.get("/status")
def get_setup_status(db: Session = Depends(get_db)):
    """Check if the initial admin user has been created."""
    user_count = db.query(user_model.User).count()
    return {"setup_complete": user_count > 0}


@router.post("/setup", response_model=user_schema.User)
def setup_admin_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    """
    Create the first admin user. This will fail if any user already exists.
    """
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
    user = crud_user.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
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
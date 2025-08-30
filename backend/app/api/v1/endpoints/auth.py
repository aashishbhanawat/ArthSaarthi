import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud
from app.core import security
from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.core.key_manager import key_manager
from app.db.session import get_db
from app.models import user as user_model
from app.schemas import token as token_schema
from app.schemas.auth import Status
from app.schemas.msg import Msg
from app.schemas.user import User, UserCreate, UserPasswordChange
from app.services.audit_logger import log_event

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
    if settings.DEPLOYMENT_MODE == "desktop":
        # In desktop mode, the creation of the first user also sets up
        # the master encryption key. This must be done *before* creating the
        # user, as the user creation will encrypt data.
        logger.info("Desktop mode: Generating and wrapping master key.")
        key_manager.generate_and_wrap_master_key(password=user.password)

    db_user = crud.user.create(db=db, obj_in=user, is_admin=True)
    db.commit()

    return db_user


@router.post("/login", response_model=token_schema.Token)
def login_for_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    logger.info(f"Login attempt for user: {form_data.username}")
    ip_address = request.client.host

    try:
        if settings.DEPLOYMENT_MODE == "desktop":
            if not key_manager.unlock_master_key(password=form_data.password):
                logger.warning(
                    f"Desktop mode login failed for user: {form_data.username} - "
                    "Master key unlock failed."
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                )

        user = crud.user.authenticate(
            db, email=form_data.username, password=form_data.password
        )
        if not user:
            logger.warning(f"Login failed for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        log_event(
            db,
            user_id=user.id,
            event_type="USER_LOGIN_SUCCESS",
            ip_address=ip_address,
        )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            subject=user.email, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "deployment_mode": settings.DEPLOYMENT_MODE,
        }
    except HTTPException as e:
        log_event(
            db,
            user_id=None,
            event_type="USER_LOGIN_FAILURE",
            ip_address=ip_address,
            details={"email": form_data.username, "reason": e.detail},
        )
        e.headers = {"WWW-Authenticate": "Bearer"}
        raise e


@router.post("/me/change-password", response_model=Msg)
def change_password(
    password_data: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_active_user),
):
    """
    Change the current user's password.
    In desktop mode, this also re-wraps the master encryption key.
    """
    # First, verify the old password is correct
    if not security.verify_password(
        password_data.old_password, current_user.hashed_password
    ):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # In desktop mode, re-wrap the master key
    if settings.DEPLOYMENT_MODE == "desktop":
        if not key_manager.change_password(
            password_data.old_password, password_data.new_password
        ):
            detail = "Failed to re-wrap master key. The old password may be incorrect."
            raise HTTPException(
                status_code=400,
                detail=detail,
            )

    # Update the password in the database
    new_hashed_password = security.get_password_hash(password_data.new_password)
    current_user.hashed_password = new_hashed_password
    db.add(current_user)
    db.commit()

    return {"msg": "Password updated successfully"}

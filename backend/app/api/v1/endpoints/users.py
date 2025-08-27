import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import crud
from app.core.dependencies import get_current_admin_user
from app.db.session import get_db
from app.models.user import User as UserModel
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.audit_logger import log_event

router = APIRouter()


@router.get("/", response_model=List[User])
def list_users(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """
    Retrieve a list of all users. (Admin Only)
    """
    users = crud.user.get_multi(db)
    return users


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """
    Create a new user. By default, new users are not admins. (Admin Only)
    """
    new_user = crud.user.create(db, obj_in=user_in)
    db.commit()
    db.refresh(new_user)

    log_event(
        db,
        user_id=current_user.id,
        event_type="USER_CREATED",
        ip_address=request.client.host,
        details={"created_user_id": new_user.id, "created_user_email": new_user.email},
    )

    return new_user


@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """
    Retrieve a user by ID. (Admin Only)
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """
    Update a user by ID. (Admin Only)
    """
    db_user = crud.user.get(db, id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = crud.user.update(db=db, db_obj=db_user, obj_in=user_in)
    db.commit()
    db.refresh(updated_user)
    return updated_user


@router.delete("/{user_id}", response_model=User)
def delete_user(
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """
    Delete a user by ID. (Admin Only)
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent deleting the admin who is deleting the user.
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself.",
        )

    deleted_user = crud.user.remove(db, id=user_id)
    db.commit()

    log_event(
        db,
        user_id=current_user.id,
        event_type="USER_DELETED",
        ip_address=request.client.host,
        details={
            "deleted_user_id": deleted_user.id,
            "deleted_user_email": deleted_user.email,
        },
    )

    return deleted_user

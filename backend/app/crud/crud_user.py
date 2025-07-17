from sqlalchemy.orm import Session
from typing import List, Optional, Any

from ..models.user import User
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from ..schemas.user import UserCreate, UserUpdate



def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 1):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate, is_admin: bool = False):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_admin=is_admin,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, *, email: str, password: str) -> Optional[User]:
    """
    Authenticates a user by email and password.
    """
    user = get_user_by_email(db, email=email)
    if not user:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user    

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Retrieve multiple users from the database.
    """
    return db.query(User).offset(skip).limit(limit).all()

def get_user(db: Session, id: int) -> Optional[User]:
    """
    Retrieve a user by ID.
    """
    return db.query(User).filter(User.id == id).first()

def update_user(db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
    """
    Update a user.
    """
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def remove(db: Session, *, id: int) -> User:
    obj = db.query(User).get(id)
    db.delete(obj)
    db.commit()
    return obj
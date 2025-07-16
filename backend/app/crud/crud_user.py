from sqlalchemy.orm import Session
from typing import Optional

from ..models.user import User
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from ..schemas.user import UserCreate


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
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
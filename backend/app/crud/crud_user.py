from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.crud.base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_user_by_email(self, db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate, is_admin: bool = False):
        hashed_password = get_password_hash(obj_in.password)
        db_user = User(
            email=obj_in.email,
            hashed_password=hashed_password,
            full_name=obj_in.full_name,
            is_admin=is_admin,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """
        Authenticates a user by email and password.
        """
        user = self.get_user_by_email(db, email=email)
        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user    

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Retrieve multiple users from the database.
        """
        return db.query(User).offset(skip).limit(limit).all()

    def get(self, db: Session, id: int) -> Optional[User]:
        """
        Retrieve a user by ID.
        """
        return db.query(User).filter(User.id == id).first()

    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
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

    def remove(self, db: Session, *, id: int) -> User:
        obj = db.get(User, id)
        db.delete(obj)
        db.commit()
        return obj

user = CRUDUser(User)

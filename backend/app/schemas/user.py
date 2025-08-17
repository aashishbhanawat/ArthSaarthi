import re
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Admin User",
                "email": "admin@example.com",
                "password": "ValidPassword123!",
            }
        }
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?:{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


# Properties to return to client
class User(UserBase):
    id: uuid.UUID
    is_admin: bool
    is_active: bool
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "full_name": "Admin User",
                "email": "admin@example.com",
                "is_active": True,
                "is_admin": True,
            }
        },
    )

class UserWithDeploymentMode(User):
    deployment_mode: Literal["single_user", "multi_user"]

# Properties to receive via API on update
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Doe Updated",
                "email": "johndoe.updated@example.com",
                "is_active": False,
                "is_admin": False,
            }
        }
    )

from pydantic import BaseModel, EmailStr, validator
import re


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

    @validator("password")
    def validate_password(cls, v):
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
    id: int
    is_admin: bool
    is_active: bool

    class Config:
        from_attributes = True
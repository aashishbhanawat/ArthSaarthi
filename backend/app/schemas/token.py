from typing import Literal

from pydantic import BaseModel

from .user import User


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User
    deployment_mode: Literal["single_user", "multi_user"]


class TokenData(BaseModel):
    email: str | None = None


class TokenPayload(BaseModel):
    sub: str | None = None

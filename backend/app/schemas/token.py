from typing import Literal

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str
    deployment_mode: Literal["server", "desktop", "android"]


class TokenData(BaseModel):
    email: str | None = None


class TokenPayload(BaseModel):
    sub: str | None = None

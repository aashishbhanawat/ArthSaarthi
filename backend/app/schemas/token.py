from pydantic import BaseModel


from typing import Literal


class Token(BaseModel):
    access_token: str
    token_type: str
    deployment_mode: Literal["server", "desktop"]


class TokenData(BaseModel):
    email: str | None = None


class TokenPayload(BaseModel):
    sub: str | None = None

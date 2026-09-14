import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BrokerCredentialSave(BaseModel):
    provider_name: str  # icici_breeze, zerodha_kite
    api_key: str
    api_secret: str


class BrokerAuthenticateRequest(BaseModel):
    provider_name: str
    session_token: str  # Breeze API session token or Kite request token


class BrokerCredentialResponse(BaseModel):
    id: uuid.UUID
    provider_name: str
    api_key: str
    is_active: bool
    is_authenticated: bool
    token_issued_at: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrokerAuthUrlResponse(BaseModel):
    provider_name: str
    login_url: str

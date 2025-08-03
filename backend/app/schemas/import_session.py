from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel


class ImportSessionBase(BaseModel):
    file_name: str
    file_path: str
    error_message: Optional[str] = None
    parsed_file_path: Optional[str] = None
    status: str


class ImportSessionCreate(ImportSessionBase):
    portfolio_id: uuid.UUID


class ImportSessionUpdate(BaseModel):
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    parsed_file_path: Optional[str] = None
    error_message: Optional[str] = None
    status: Optional[str] = None


class ImportSessionInDBBase(ImportSessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    portfolio_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ImportSession(ImportSessionInDBBase):
    pass

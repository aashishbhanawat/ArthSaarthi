from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict


class ImportSessionBase(BaseModel):
    file_name: str
    file_path: str
    parsed_file_path: Optional[str] = None
    status: str


class ImportSessionCreate(ImportSessionBase):
    pass


class ImportSessionUpdate(ImportSessionBase):
    pass


class ImportSessionInDBBase(ImportSessionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ImportSession(ImportSessionInDBBase):
    pass


class ImportSessionInDB(ImportSessionInDBBase):
    pass

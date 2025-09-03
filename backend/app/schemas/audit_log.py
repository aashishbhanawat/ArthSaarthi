import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


# Base schema for audit log entries
class AuditLogBase(BaseModel):
    event_type: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_id: Optional[uuid.UUID] = None


# Schema for creating new audit log entries
class AuditLogCreate(AuditLogBase):
    pass


# Schema for reading audit log entries, includes fields from the database model
class AuditLog(AuditLogBase):
    id: uuid.UUID
    timestamp: datetime

    class Config:
        from_attributes = True

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel
from pydantic.version import VERSION

try:
    if VERSION.startswith("2."):
        from pydantic import ConfigDict
    else:
        ConfigDict = None
except ImportError:
    ConfigDict = None


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

    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


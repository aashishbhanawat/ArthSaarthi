import uuid
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app import crud
from app.schemas.audit_log import AuditLogCreate


def log_event(
    db: Session,
    *,
    user_id: Optional[uuid.UUID],
    event_type: str,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Logs an audit event to the database.
    """
    audit_log_in = AuditLogCreate(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        details=details,
    )
    crud.audit_log.create(db, obj_in=audit_log_in)

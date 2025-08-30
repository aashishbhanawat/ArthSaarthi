from app.crud.base import CRUDBase
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate


# Note: Audit logs are typically not updated, so we don't need a specific update schema.
# We can reuse AuditLogCreate, but in practice, update operations might be disallowed.
class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, AuditLogCreate]):
    pass

audit_log = CRUDAuditLog(AuditLog)

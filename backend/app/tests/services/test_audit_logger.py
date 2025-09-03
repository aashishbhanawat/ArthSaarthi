import uuid
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.schemas.audit_log import AuditLogCreate
from app.services.audit_logger import log_event


def test_log_event():
    """
    Test that log_event calls crud.audit_log.create with the correct data.
    """
    db = MagicMock(spec=Session)
    user_id = uuid.uuid4()
    event_type = "TEST_EVENT"
    ip_address = "127.0.0.1"
    details = {"key": "value"}

    with patch("app.crud.audit_log.create") as mock_create:
        log_event(
            db,
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            details=details,
        )

        mock_create.assert_called_once()
        pos_args, kw_args = mock_create.call_args
        assert pos_args[0] == db
        created_log = kw_args["obj_in"]
        assert isinstance(created_log, AuditLogCreate)
        assert created_log.user_id == user_id
        assert created_log.event_type == event_type
        assert created_log.ip_address == ip_address
        assert created_log.details == details

import logging
import os
import subprocess
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.import_parsers.broker_api_parser import (
    parse_icici_api_payload,
    parse_zerodha_api_payload,
)
from app.tests.utils.user import create_random_user, get_access_token

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_broker_api_parser_does_not_log_raw_pii(caplog):
    """Verify issue #601: raw broker API item values are never logged at DEBUG level."""
    zerodha_item = {"tradingsymbol": "INFY", "isin": "INE009A01021", "quantity": 10, "average_price": 1500.0}
    icici_item = {"stock_code": "INFY", "quantity": 5, "average_price": 1400.0, "account_id": "SECRET_PAN_123"}

    with caplog.at_level(logging.DEBUG, logger="app.services.import_parsers.broker_api_parser"):
        parse_zerodha_api_payload([zerodha_item], import_type="holdings")
        parse_icici_api_payload([icici_item], import_type="holdings")
        parse_icici_api_payload([icici_item], import_type="trades")

    log_text = caplog.text
    assert "SECRET_PAN_123" not in log_text
    assert "INE009A01021" not in log_text
    assert "raw sample (first item keys)" in log_text


def test_inspect_icici_raw_blocks_production():
    """Verify issue #602: inspect_icici_raw.py refuses to run when ENVIRONMENT=production."""
    env = dict(os.environ)
    env["ENVIRONMENT"] = "production"
    res = subprocess.run(
        [sys.executable, "/app/scripts/inspect_icici_raw.py"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "must NOT be run in production" in res.stdout


def test_system_logs_and_snapshots_require_admin_in_server_mode(
    client: TestClient,
    db: Session,
):
    """Verify issue #603: /system/logs and /system/snapshots/run-daily enforce admin auth."""
    regular_user, reg_pw = create_random_user(db, is_admin=False)
    admin_user, admin_pw = create_random_user(db, is_admin=True)
    reg_headers = {"Authorization": f"Bearer {get_access_token(client, regular_user.email, reg_pw)}"}
    admin_headers = {"Authorization": f"Bearer {get_access_token(client, admin_user.email, admin_pw)}"}

    # Unauthenticated -> 401
    assert client.get("/api/v1/system/logs").status_code == 401
    assert client.post("/api/v1/system/snapshots/run-daily").status_code == 401

    # Non-admin -> 403
    assert client.get("/api/v1/system/logs", headers=reg_headers).status_code == 403
    assert client.post("/api/v1/system/snapshots/run-daily", headers=reg_headers).status_code == 403

    # Admin -> 200
    assert client.get("/api/v1/system/logs", headers=admin_headers).status_code == 200
    with patch("app.api.v1.endpoints.system.take_daily_snapshots_for_all", return_value=0):
        res_snap = client.post("/api/v1/system/snapshots/run-daily", headers=admin_headers)
        assert res_snap.status_code == 200
        assert res_snap.json()["updated"] == 0

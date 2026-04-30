"""
API tests for system endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import os

from app.core.config import settings
from app.tests.utils.user import create_random_user, get_access_token

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")

API_PREFIX = f"{settings.API_V1_STR}/system"

def _admin_headers(client: TestClient, db: Session) -> dict:
    """Helper to create an admin user and return auth headers."""
    admin_user, admin_password = create_random_user(db, is_admin=True)
    token = get_access_token(client, admin_user.email, admin_password)
    return {"Authorization": f"Bearer {token}"}

def _non_admin_headers(client: TestClient, db: Session) -> dict:
    user, password = create_random_user(db, is_admin=False)
    token = get_access_token(client, user.email, password)
    return {"Authorization": f"Bearer {token}"}

def test_get_logs_non_admin(client: TestClient, db: Session) -> None:
    headers = _non_admin_headers(client, db)
    response = client.get(f"{API_PREFIX}/logs", headers=headers)
    assert response.status_code == 403

def test_get_logs_admin_no_log_file(client: TestClient, db: Session, monkeypatch) -> None:
    headers = _admin_headers(client, db)
    monkeypatch.setattr(settings, "LOG_FILE", None)
    response = client.get(f"{API_PREFIX}/logs", headers=headers)
    assert response.status_code == 200
    assert response.json()["msg"] == "Logging to file is not enabled in this mode."

def test_get_logs_admin_missing_file(client: TestClient, db: Session, monkeypatch) -> None:
    headers = _admin_headers(client, db)
    monkeypatch.setattr(settings, "LOG_FILE", "/tmp/does_not_exist.log")
    response = client.get(f"{API_PREFIX}/logs", headers=headers)
    assert response.status_code == 200
    assert response.json()["msg"] == "Log file not found"

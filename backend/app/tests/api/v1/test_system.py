import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.user import create_random_user, get_access_token

def test_get_logs_admin(
    client: TestClient, db: Session
) -> None:
    # Create an admin user
    user, password = create_random_user(db, is_admin=True)
    access_token = get_access_token(client, user.email, password)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Ensure LOG_FILE is set for testing
    import os
    from pathlib import Path
    
    test_log = Path("test_system.log")
    test_log.write_text("line1\nline2\nline3")
    
    original_log_file = settings.LOG_FILE
    settings.LOG_FILE = str(test_log)
    
    try:
        r = client.get(
            f"{settings.API_V1_STR}/system/logs", headers=headers,
        )
        assert r.status_code == 200
        assert "line1\nline2\nline3" in r.json()["msg"]
    finally:
        settings.LOG_FILE = original_log_file
        if test_log.exists():
            test_log.unlink()


def test_get_logs_non_admin(
    client: TestClient, db: Session
) -> None:
    # Create a regular user
    user, password = create_random_user(db, is_admin=False)
    access_token = get_access_token(client, user.email, password)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    r = client.get(
        f"{settings.API_V1_STR}/system/logs", headers=headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Not an admin user"


def test_get_logs_no_file(
    client: TestClient, db: Session
) -> None:
    user, password = create_random_user(db, is_admin=True)
    access_token = get_access_token(client, user.email, password)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    original_log_file = settings.LOG_FILE
    settings.LOG_FILE = "non_existent_file.log"
    
    try:
        r = client.get(
            f"{settings.API_V1_STR}/system/logs", headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["msg"] == "Log file not found"
    finally:
        settings.LOG_FILE = original_log_file

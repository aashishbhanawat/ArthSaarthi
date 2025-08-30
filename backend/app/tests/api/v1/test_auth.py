import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.user import User as UserModel


def test_get_status_setup_needed(client: TestClient):
    response = client.get("/api/v1/auth/status")
    assert response.status_code == 200
    assert response.json() == {"setup_needed": True}, (
        "Should indicate setup is needed initially"
    )
    assert response.headers["content-type"] == "application/json"


def test_setup_admin_user_success(client: TestClient):
    user_data = {
        "full_name": "Admin User",
        "email": "admin@example.com",
        "password": "ValidPassword123!",
    }
    response = client.post("/api/v1/auth/setup", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data


def test_get_status_setup_not_needed(client: TestClient):
    # Arrange: Create a user first to ensure setup is not needed.
    user_data = {
        "full_name": "Admin User",
        "email": "admin@example.com",
        "password": "ValidPassword123!",
    }
    client.post("/api/v1/auth/setup", json=user_data)

    # Act
    response = client.get("/api/v1/auth/status")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"setup_needed": False}


def test_setup_admin_user_fails_if_user_exists(client: TestClient):
    # Arrange: Create the first admin user.
    first_user_data = {
        "full_name": "Admin User",
        "email": "admin@example.com",
        "password": "ValidPassword123!",
    }
    client.post("/api/v1/auth/setup", json=first_user_data)

    # Act: Attempt to create a second user.
    second_user_data = {
        "full_name": "Another User",
        "email": "another@example.com",
        "password": "ValidPassword123!",
    }
    response = client.post("/api/v1/auth/setup", json=second_user_data)

    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "An admin account already exists."}


def test_login_success_creates_audit_log(
    client: TestClient, db: Session, admin_user_data: dict
):
    # Arrange: Create the user
    user_response = client.post("/api/v1/auth/setup", json=admin_user_data)
    user_id = user_response.json()["id"]

    # Act: Log in
    login_data = {
        "username": admin_user_data["email"],
        "password": admin_user_data["password"],
    }
    response = client.post("/api/v1/auth/login", data=login_data)

    # Assert: Check token and audit log
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"

    log_entry = db.query(AuditLog).filter_by(event_type="USER_LOGIN_SUCCESS").first()
    assert log_entry is not None
    assert str(log_entry.user_id) == user_id
    assert log_entry.ip_address == "testclient"


def test_login_wrong_password_creates_audit_log(
    client: TestClient, db: Session, admin_user_data: dict
):
    # Arrange: Create user
    client.post("/api/v1/auth/setup", json=admin_user_data)

    # Act: Attempt login with wrong password
    login_data = {"username": admin_user_data["email"], "password": "wrongpassword!1"}
    response = client.post("/api/v1/auth/login", data=login_data)

    # Assert: Check response and audit log
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

    log_entry = db.query(AuditLog).filter_by(event_type="USER_LOGIN_FAILURE").first()
    assert log_entry is not None
    assert log_entry.user_id is None
    assert log_entry.ip_address == "testclient"
    assert log_entry.details["email"] == admin_user_data["email"]


def test_login_nonexistent_user(client: TestClient):
    login_data = {
        "username": "nonexistent@example.com",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.skipif(
    settings.DEPLOYMENT_MODE == "desktop",
    reason="Inactive user concept is not applicable in single-user desktop mode.",
)
def test_login_inactive_user(client: TestClient, db: Session, admin_user_data: dict):
    # Arrange: Create a user
    client.post("/api/v1/auth/setup", json=admin_user_data)
    user_email = admin_user_data["email"]

    # Manually set the user to inactive in the database
    user_in_db = db.query(UserModel).filter(UserModel.email == user_email).first()
    assert user_in_db is not None
    user_in_db.is_active = False
    db.commit()

    # Act: Attempt to log in
    login_data = {
        "username": admin_user_data["email"],
        "password": admin_user_data["password"],
    }
    response = client.post("/api/v1/auth/login", data=login_data)

    # Assert
    assert response.status_code == 401


@pytest.mark.parametrize(
    "password, error_message_part",
    [
        ("weak", "at least 8 characters long"),
        ("NoNumber!", "at least one number"),
        ("nonumber1", "at least one uppercase letter"),
        ("NONUMBER1", "at least one lowercase letter"),
        ("NoSpecial1", "at least one special character"),
    ],
)
def test_setup_admin_user_invalid_password(
    client: TestClient, password: str, error_message_part: str
):
    # Arrange
    user_data = {
        "full_name": "Test User",
        "email": "test@example.com",
        "password": password,
    }

    # Act
    response = client.post("/api/v1/auth/setup", json=user_data)

    # Assert
    assert response.status_code == 422
    assert "detail" in response.json()


def test_change_password_success(client: TestClient, db: Session, admin_user_data: dict):
    # Arrange: Create and log in user
    user_response = client.post("/api/v1/auth/setup", json=admin_user_data)
    assert user_response.status_code == 200

    login_data = {
        "username": admin_user_data["email"],
        "password": admin_user_data["password"],
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Act: Change password
    new_password = "NewValidPassword123!"
    change_password_data = {
        "old_password": admin_user_data["password"],
        "new_password": new_password,
    }
    response = client.post(
        "/api/v1/auth/me/change-password",
        headers=headers,
        json=change_password_data,
    )

    # Assert: Check response
    assert response.status_code == 200
    assert response.json() == {"msg": "Password updated successfully"}

    # Verify new password works for login
    new_login_data = {"username": admin_user_data["email"], "password": new_password}
    response = client.post("/api/v1/auth/login", data=new_login_data)
    assert response.status_code == 200


def test_change_password_incorrect_old_password(
    client: TestClient, db: Session, admin_user_data: dict
):
    # Arrange: Create and log in user
    user_response = client.post("/api/v1/auth/setup", json=admin_user_data)
    assert user_response.status_code == 200

    login_data = {
        "username": admin_user_data["email"],
        "password": admin_user_data["password"],
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Act: Attempt to change password with incorrect old password
    change_password_data = {
        "old_password": "wrongoldpassword",
        "new_password": "NewValidPassword123!",
    }
    response = client.post(
        "/api/v1/auth/me/change-password",
        headers=headers,
        json=change_password_data,
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect old password"}

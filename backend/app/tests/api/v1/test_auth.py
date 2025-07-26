import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.models.user import User as UserModel

from app import crud, models, schemas  # Keep these for now, but might be unused
from app.core import security       # Keep this as it's used directly
from app.tests.utils.user import create_random_user, get_access_token

def test_get_status_setup_needed(client: TestClient):
    response = client.get("/api/v1/auth/status")
    assert response.status_code == 200
    assert response.json() == {"setup_needed": True}, "Should indicate setup is needed initially"
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


def test_login_success(client: TestClient, admin_user_data: dict):
    # First, create the user via the setup endpoint
    client.post("/api/v1/auth/setup", json=admin_user_data)

    # Then, attempt to log in
    login_data = {
        "username": admin_user_data["email"],
        "password": admin_user_data["password"],
    }
    response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, admin_user_data: dict):
    client.post("/api/v1/auth/setup", json=admin_user_data)
    login_data = {"username": admin_user_data["email"], "password": "wrongpassword!1"}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_nonexistent_user(client: TestClient):
    login_data = {
        "username": "nonexistent@example.com",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_inactive_user(client: TestClient, db: Session, admin_user_data: dict):
    # Arrange: Create a user
    response = client.post("/api/v1/auth/setup", json=admin_user_data)
    user_email = response.json()["email"]

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
    assert response.status_code == 422  # Expect a validation error
    assert "detail" in response.json()  # Check for error details

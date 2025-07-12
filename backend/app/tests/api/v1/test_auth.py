from fastapi.testclient import TestClient
import pytest


def test_get_status_setup_needed(client: TestClient):
    response = client.get("/api/v1/auth/status")
    assert response.status_code == 200
    assert response.json() == {"setup_needed": True}


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
    assert error_message_part in response.text
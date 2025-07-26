from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.utils.user import create_random_user


def test_get_current_user_unauthorized(client: TestClient):
    """
    Test that an unauthenticated user cannot access their profile.
    """
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_get_current_user_success(client: TestClient, db: Session, get_auth_headers):
    """
    Test successfully retrieving the current user's profile.
    """
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email


def test_get_current_user_invalid_token(client: TestClient):
    """
    Test handling of an invalid authentication token.
    """
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401
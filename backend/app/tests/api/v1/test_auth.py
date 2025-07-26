from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.user import create_random_user
from app.core import security


def test_refresh_token_success(client: TestClient, db: Session):
    """
    Test successfully getting a new access token using a valid refresh token.
    """
    user, password = create_random_user(db)

    # First, log in to get the refresh token cookie
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": user.email, "password": password},
    )
    assert login_response.status_code == 200
    refresh_cookie = login_response.cookies.get("refresh_token")
    assert refresh_cookie is not None

    # Now, use the cookie to call the refresh endpoint
    client.cookies.set("refresh_token", refresh_cookie)
    refresh_response = client.post(f"{settings.API_V1_STR}/auth/refresh")
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_no_cookie(client: TestClient):
    """
    Test that the refresh endpoint fails with 401 if no cookie is provided.
    """
    response = client.post(f"{settings.API_V1_STR}/auth/refresh")
    assert response.status_code == 401
    assert "no refresh token found" in response.json()["detail"]


def test_refresh_token_invalid_cookie(client: TestClient):
    """
    Test that the refresh endpoint fails with 401 if the cookie is invalid.
    """
    client.cookies.set("refresh_token", "invalid-token")
    response = client.post(f"{settings.API_V1_STR}/auth/refresh")
    assert response.status_code == 401
    assert "token is invalid or expired" in response.json()["detail"]


def test_refresh_token_with_access_token(client: TestClient, db: Session):
    """
    Test that the refresh endpoint fails if an access token is used instead of a refresh token.
    """
    user, _ = create_random_user(db)
    access_token = security.create_access_token(subject=user.id)

    client.cookies.set("refresh_token", access_token)
    response = client.post(f"{settings.API_V1_STR}/auth/refresh")
    assert response.status_code == 401
    assert "Invalid token type" in response.json()["detail"]


def test_logout_success(client: TestClient, db: Session):
    """
    Test that logout successfully clears the refresh token cookie.
    """
    user, password = create_random_user(db)

    # Log in to set the cookie
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": user.email, "password": password},
    )
    assert login_response.cookies.get("refresh_token") is not None

    # Call logout
    client.cookies.set("refresh_token", login_response.cookies.get("refresh_token"))
    logout_response = client.post(f"{settings.API_V1_STR}/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Successfully logged out"

    # Check that the cookie is cleared in the response headers
    set_cookie_header = logout_response.headers.get("set-cookie")
    assert set_cookie_header is not None
    # A cleared cookie has Max-Age=0 and an empty value
    assert 'refresh_token=""' in set_cookie_header
    assert "Max-Age=0" in set_cookie_header


def test_logout_no_cookie(client: TestClient):
    """
    Test that logout succeeds even if no cookie is present.
    """
    response = client.post(f"{settings.API_V1_STR}/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"
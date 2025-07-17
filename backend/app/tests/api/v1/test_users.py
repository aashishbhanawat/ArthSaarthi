from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.utils.user import create_random_user, get_access_token




def test_get_current_user_unauthorized(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated", "Should return 401 for unauthorized access"


def test_get_current_user_success(
    client: TestClient, db: Session, get_auth_headers
):
    """
    Test successfully retrieving the current user's profile.
    """
    # 1. Arrange: Create a user using the utility function and get their access token.
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    # 2. Act: Call the endpoint to get the current user's profile using the obtained token.
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    returned_user = response.json()  # API response is now correctly assigned to returned_user
    # 3. Assert: Verify that the returned user data matches the created user's data.
    assert returned_user["email"] == user.email  # Comparison is now correct.
    assert returned_user["full_name"] == user.full_name
    assert returned_user["id"] == user.id


def test_get_current_user_invalid_token(client: TestClient):
    """
    Test handling of an invalid authentication token.
    """
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 403
    assert (
        response.json()["detail"] == "Could not validate credentials"
    ), "Should return 403 for invalid token"
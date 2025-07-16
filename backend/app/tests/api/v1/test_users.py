from fastapi.testclient import TestClient


def test_get_current_user_unauthorized(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def get_auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    login_data = {"username": email, "password": password}
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_current_user_success(client: TestClient, admin_user_data: dict):
    # Create user first
    client.post("/api/v1/auth/setup", json=admin_user_data)

    # Get token and create headers
    headers = get_auth_headers(
        client, admin_user_data["email"], admin_user_data["password"]
    )

    # Test the protected endpoint
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == admin_user_data["email"]
    assert user["full_name"] == admin_user_data["full_name"]


def test_get_current_user_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Could not validate credentials"
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud.crud_broker import crud_broker
from app.models.user import User


def test_broker_credentials_crud_and_endpoints(
    client: TestClient, get_auth_headers, db: Session
):
    # 1. Setup admin user
    user_data = {
        "full_name": "Test User",
        "email": "testbroker@example.com",
        "password": "ValidPassword123!",
    }
    setup_resp = client.post("/api/v1/auth/setup", json=user_data)
    assert setup_resp.status_code == 200

    headers = get_auth_headers("testbroker@example.com", "ValidPassword123!")
    user_obj = db.query(User).filter(User.email == "testbroker@example.com").first()
    assert user_obj is not None

    # 2. Get credentials initially (empty)
    resp = client.get("/api/v1/broker/credentials", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []

    # 3. Save ICICI Breeze credentials
    payload = {
        "provider_name": "icici_breeze",
        "api_key": "test_icici_key_123",
        "api_secret": "test_icici_secret_456",
    }
    resp = client.post(
        "/api/v1/broker/credentials", json=payload, headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider_name"] == "icici_breeze"
    assert data["api_key"] == "test_icici_key_123"
    assert data["is_authenticated"] is False
    assert "api_secret" not in data

    # 4. Verify encrypted storage in DB
    db_obj = crud_broker.get_by_user_and_provider(db, user_id=user_obj.id, provider_name="icici_breeze")
    assert db_obj is not None
    assert db_obj.api_key == "test_icici_key_123"
    assert db_obj.encrypted_api_secret != "test_icici_secret_456"
    decrypted_secret = crud_broker.get_decrypted_secret(db_obj)
    assert decrypted_secret == "test_icici_secret_456"

    # 5. Get ICICI login URL
    resp = client.get("/api/v1/broker/icici/login-url", headers=headers)
    assert resp.status_code == 200
    url_data = resp.json()
    assert "https://api.icicidirect.com/apihandler/index.html?API_KEY=test_icici_key_123" in url_data["login_url"]

    # 6. Authenticate ICICI Breeze session (mocking provider response)
    with patch(
        "app.services.providers.icici_breeze_provider.IciciBreezeProvider.authenticate_session",
        return_value={"success": True, "data": {"session_token": "valid_session_789"}},
    ):
        auth_payload = {
            "provider_name": "icici_breeze",
            "session_token": "valid_session_789",
        }
        resp = client.post(
            "/api/v1/broker/icici/authenticate",
            json=auth_payload,
            headers=headers,
        )
        assert resp.status_code == 200
        auth_data = resp.json()
        assert auth_data["is_authenticated"] is True

    # 7. Delete broker credentials
    resp = client.delete(
        "/api/v1/broker/credentials/icici_breeze",
        headers=headers,
    )
    assert resp.status_code == 200
    assert "Successfully deleted" in resp.json()["message"]

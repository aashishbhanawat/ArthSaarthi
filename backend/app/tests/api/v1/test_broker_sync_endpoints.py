from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings


def test_broker_sync_endpoint_unauthenticated_broker(client: TestClient, db: Session, get_auth_headers):
    user_in = schemas.UserCreate(
        email="sync_user@example.com",
        password="ValidPassword123!",
        full_name="Sync User",
    )
    user = crud.user.create(db=db, obj_in=user_in)
    headers = get_auth_headers("sync_user@example.com", "ValidPassword123!")

    portfolio = crud.portfolio.create_with_owner(
        db=db,
        obj_in=schemas.PortfolioCreate(name="Broker Sync Test Portfolio", description="Test"),
        user_id=user.id,
    )

    payload = {
        "provider_name": "icici_breeze",
        "portfolio_id": str(portfolio.id),
        "import_type": "holdings",
    }

    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/broker/sync",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 401
    assert "No active session" in response.json()["detail"]


def test_broker_sync_endpoint_zerodha_disabled(client: TestClient, db: Session, get_auth_headers):
    user_in = schemas.UserCreate(
        email="sync_zerodha_user@example.com",
        password="ValidPassword123!",
        full_name="Zerodha User",
    )
    user = crud.user.create(db=db, obj_in=user_in)
    headers = get_auth_headers("sync_zerodha_user@example.com", "ValidPassword123!")

    portfolio = crud.portfolio.create_with_owner(
        db=db,
        obj_in=schemas.PortfolioCreate(name="Broker Sync Zerodha Portfolio", description="Test"),
        user_id=user.id,
    )

    mock_cred = MagicMock()
    mock_cred.is_active = True
    mock_cred.encrypted_access_token = "encrypted_token"
    mock_cred.token_expires_at = None
    mock_cred.api_key = "test_key"

    with patch.object(crud.crud_broker, "get_by_user_and_provider", return_value=mock_cred), \
         patch.object(crud.crud_broker, "get_decrypted_token", return_value="token123"), \
         patch.object(crud.crud_broker, "get_decrypted_secret", return_value="secret123"):
        response = client.post(
            f"{settings.API_V1_STR}/import-sessions/broker/sync",
            headers=headers,
            json={
                "provider_name": "zerodha_kite",
                "portfolio_id": str(portfolio.id),
                "import_type": "holdings",
            },
        )
        assert response.status_code == 400
        assert "disabled for Zerodha Kite" in response.json()["detail"]


@patch.object(crud.crud_broker, "get_by_user_and_provider")
@patch.object(crud.crud_broker, "get_decrypted_token")
@patch.object(crud.crud_broker, "get_decrypted_secret")
@patch("app.services.providers.icici_breeze_provider.IciciBreezeProvider.fetch_holdings")
def test_broker_sync_endpoint_success(
    mock_fetch_holdings,
    mock_dec_secret,
    mock_dec_token,
    mock_get_cred,
    client: TestClient,
    db: Session,
    get_auth_headers,
):
    user_in = schemas.UserCreate(
        email="sync_user_success@example.com",
        password="ValidPassword123!",
        full_name="Sync User 2",
    )
    user = crud.user.create(db=db, obj_in=user_in)
    headers = get_auth_headers("sync_user_success@example.com", "ValidPassword123!")

    portfolio = crud.portfolio.create_with_owner(
        db=db,
        obj_in=schemas.PortfolioCreate(name="Broker Sync Success Portfolio", description="Test"),
        user_id=user.id,
    )

    mock_cred = MagicMock()
    mock_cred.is_active = True
    mock_cred.encrypted_access_token = "encrypted_token"
    mock_cred.token_expires_at = None
    mock_cred.api_key = "test_key"
    mock_get_cred.return_value = mock_cred
    mock_dec_token.return_value = "access_token_123"
    mock_dec_secret.return_value = "secret_123"

    mock_fetch_holdings.return_value = [
        {
            "stock_code": "WIPRO",
            "exchange_code": "NSE",
            "quantity": 50,
            "average_price": 420.00,
        }
    ]

    payload = {
        "provider_name": "icici_breeze",
        "portfolio_id": str(portfolio.id),
        "import_type": "holdings",
    }

    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/broker/sync",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "icici_breeze_api"
    assert data["status"] == "PARSED"

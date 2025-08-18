import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.services.financial_data_service import financial_data_service
from app.tests.utils.asset import create_test_asset
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_create_asset_success(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    """
    Test successful creation of a new asset that does not exist locally.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    ticker_to_create = "NEWTICKER"

    # Mock the external service to return valid details
    mock_asset_details = {
        "name": "New Ticker Inc.",
        "asset_type": "Stock",
        "exchange": "NASDAQ",
        "currency": "USD",
    }
    mocker.patch.object(
        financial_data_service, "get_asset_details", return_value=mock_asset_details
    )

    # Make the API call
    response = client.post(
        f"{settings.API_V1_STR}/assets/",
        headers=auth_headers,
        json={"ticker_symbol": ticker_to_create},
    )

    # Assertions
    assert response.status_code == 201
    data = response.json()
    assert data["ticker_symbol"] == ticker_to_create
    assert data["name"] == "New Ticker Inc."
    assert data["exchange"] == "NASDAQ"

    # Verify it's in the database
    db_asset = crud.asset.get(db, id=data["id"])
    assert db_asset is not None
    assert db_asset.ticker_symbol == ticker_to_create


def test_create_asset_conflict(client: TestClient, db: Session, get_auth_headers):
    """
    Test attempting to create an asset that already exists in the database.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    # Pre-create an asset in the DB
    existing_ticker = "EXISTING"
    create_test_asset(db, ticker_symbol=existing_ticker)

    response = client.post(
        f"{settings.API_V1_STR}/assets/",
        headers=auth_headers,
        json={"ticker_symbol": existing_ticker},
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_asset_not_found_externally(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    """
    Test attempting to create an asset that is not found by the external service.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    mocker.patch.object(financial_data_service, "get_asset_details", return_value=None)

    response = client.post(
        f"{settings.API_V1_STR}/assets/",
        headers=auth_headers,
        json={"ticker_symbol": "INVALIDTICKER"},
    )

    assert response.status_code == 404
    assert "Could not find a valid asset" in response.json()["detail"]


def test_create_asset_unauthorized(client: TestClient):
    """
    Test that an unauthenticated user cannot create an asset.
    """
    response = client.post(
        f"{settings.API_V1_STR}/assets/",
        json={"ticker_symbol": "ANYTICKER"},
    )
    assert response.status_code == 401

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.core.config import settings
from app.services.financial_data_service import financial_data_service
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


# Mock data for the financial_data_service search
MOCK_SEARCH_RESULTS = [
    {
        "ticker_symbol": "100033",
        "name": "Axis Bluechip Fund - Direct Plan - Growth",
        "asset_type": "Mutual Fund",
    },
    {
        "ticker_symbol": "120503",
        "name": "HDFC Index Fund - S&P BSE Sensex Plan - Direct Plan",
        "asset_type": "Mutual Fund",
    },
]


def test_search_mutual_funds_success(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    """
    Test successful search for mutual funds.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    # Mock the service layer call
    mocker.patch.object(
        financial_data_service, "search_mutual_funds", return_value=MOCK_SEARCH_RESULTS
    )

    response = client.get(
        f"{settings.API_V1_STR}/assets/search-mf/?q=axis", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["ticker_symbol"] == "100033"
    assert data[0]["name"] == "Axis Bluechip Fund - Direct Plan - Growth"
    financial_data_service.search_mutual_funds.assert_called_once_with(query="axis")


def test_search_mutual_funds_no_results(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    """
    Test search for mutual funds that returns no results.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    mocker.patch.object(financial_data_service, "search_mutual_funds", return_value=[])

    response = client.get(
        f"{settings.API_V1_STR}/assets/search-mf/?q=nonexistent", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json() == []


def test_search_mutual_funds_unauthorized(client: TestClient):
    """
    Test that an unauthenticated user cannot search for mutual funds.
    """
    response = client.get(f"{settings.API_V1_STR}/assets/search-mf/?q=any")
    assert response.status_code == 401


def test_search_mutual_funds_query_too_short(
    client: TestClient, db: Session, get_auth_headers
):
    """
    Test that the search query must meet the minimum length requirement.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    response = client.get(
        f"{settings.API_V1_STR}/assets/search-mf/?q=ax", headers=auth_headers
    )
    assert response.status_code == 422  # Unprocessable Entity for validation error

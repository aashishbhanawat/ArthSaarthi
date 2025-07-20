from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from app.core.config import settings
from app.tests.utils.user import create_random_user
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction


def test_get_dashboard_summary_unauthorized(client: TestClient):
    """
    Test that an unauthenticated user receives a 401 Unauthorized error.
    """
    response = client.get(f"{settings.API_V1_STR}/dashboard/summary")
    assert response.status_code == 401


def test_get_dashboard_summary_no_portfolios(
    client: TestClient, db: Session, get_auth_headers
):
    """
    Test that a user with no portfolios receives an empty summary.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    response = client.get(f"{settings.API_V1_STR}/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_value"] == '0.0'
    assert data["total_unrealized_pnl"] == '0.0'
    assert data["total_realized_pnl"] == '0.0'
    assert data["top_movers"] == []


def test_get_dashboard_summary_success(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    """
    Test successful retrieval and calculation of a dashboard summary.
    """
    # 1. Setup User and Auth
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    # 2. Mock FinancialDataService to return predictable prices
    mock_get_price = MagicMock()
    mock_get_price.side_effect = lambda ticker: {
        "AAPL": {"price": 150.0},
        "GOOG": {"price": 2800.0},
        "BTC": {"price": 45000.0},
    }.get(ticker, {"price": 0.0})

    mocker.patch(
        "app.crud.crud_dashboard.FinancialDataService.get_asset_price",
        new=mock_get_price,
    )

    # 3. Create test data
    portfolio1 = create_test_portfolio(db, user_id=user.id, name="Tech Stocks")
    create_test_transaction(db, portfolio_id=portfolio1.id, ticker="AAPL", quantity=10, asset_type="Stock")  # Value: 1500
    create_test_transaction(db, portfolio_id=portfolio1.id, ticker="GOOG", quantity=2, asset_type="Stock")   # Value: 5600

    portfolio2 = create_test_portfolio(db, user_id=user.id, name="Crypto")
    create_test_transaction(db, portfolio_id=portfolio2.id, ticker="BTC", quantity=0.5, asset_type="Crypto") # Value: 22500

    # 4. Make API call
    response = client.get(f"{settings.API_V1_STR}/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # 5. Assertions - The total value is 10 * 150.0 + 2 * 2800.0 + 0.5 * 45000.0 = 1500 + 5600 + 22500 = 29600
    assert float(data["total_value"]) == 29600.0
    # Assert placeholder values from the current implementation
    assert data["total_unrealized_pnl"] == "0.0"
    assert data["total_realized_pnl"] == "0.0"
    assert data["top_movers"] == []


def test_get_dashboard_summary_with_failing_price_lookup(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    """
    Test that the summary calculation handles assets where price lookup fails.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    mock_get_price = MagicMock(side_effect=Exception("API lookup failed"))
    mocker.patch("app.crud.crud_dashboard.FinancialDataService.get_asset_price", new=mock_get_price)

    portfolio = create_test_portfolio(db, user_id=user.id, name="Failing Portfolio")
    create_test_transaction(db, portfolio_id=portfolio.id, ticker="FAIL", quantity=10, asset_type="Stock")

    response = client.get(f"{settings.API_V1_STR}/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # The failing asset should be valued at 0
    assert float(data["total_value"]) == 0.0
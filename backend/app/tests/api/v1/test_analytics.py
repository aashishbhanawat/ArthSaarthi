from datetime import date, timedelta
from decimal import Decimal
import uuid
from typing import Dict

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app import schemas
from app.core.config import settings
from app.crud import crud_user
from app.schemas.analytics import AnalyticsResponse
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.tests.utils.user import create_random_user
from app.services.financial_data_service import financial_data_service


def test_get_portfolio_analytics_success(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """
    Test successful retrieval of portfolio analytics.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(email=user.email, password=password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Analytics Portfolio")

    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/analytics", headers=auth_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert "xirr" in content
    assert "sharpe_ratio" in content


def test_get_portfolio_analytics_not_found(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """
    Test that a 404 is returned for a non-existent portfolio.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(email=user.email, password=password)
    portfolio_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio_id}/analytics", headers=auth_headers
    )
    assert response.status_code == 404


def test_get_portfolio_analytics_unauthorized(client: TestClient, db: Session) -> None:
    """
    Test getting analytics without authentication.
    """
    response = client.get(f"{settings.API_V1_STR}/portfolios/{uuid.uuid4()}/analytics")
    assert response.status_code == 401


def test_get_portfolio_analytics_forbidden(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """
    Test that a 403 is returned when trying to access another user's portfolio analytics.
    """
    # User who makes the request
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(email=user.email, password=password)

    # A portfolio owned by another user
    other_user, _ = create_random_user(db)
    other_portfolio = create_test_portfolio(db, user_id=other_user.id, name="Other User Portfolio")

    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{other_portfolio.id}/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_get_portfolio_analytics_calculation(
    client: TestClient, db: Session, get_auth_headers, mocker
) -> None:
    """
    Test the XIRR and Sharpe Ratio calculation with sample data.
    """
    # 1. Mock date.today() to have a predictable end date for XIRR calculation
    fixed_today = date(2024, 8, 1)
    mocker.patch("app.crud.crud_analytics.date").today.return_value = fixed_today

    # 2. Setup User, Portfolio, and Auth
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(email=user.email, password=password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Calculation Portfolio")

    # 3. Setup Transactions to create a cash flow history
    # Buy 10 of CALC1 at 100 one year ago
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="CALC1",
        quantity=Decimal(10),
        price_per_unit=Decimal(100),
        transaction_type="BUY",
        transaction_date=fixed_today - timedelta(days=365),
    )

    # 4. Mock external dependencies
    # Mock current prices for the final value calculation in XIRR
    mock_prices = {
        "CALC1": {"current_price": Decimal("110.0"), "previous_close": Decimal("109.0")}
    }
    mocker.patch.object(financial_data_service, "get_current_prices", return_value=mock_prices)

    # Mock historical prices for Sharpe Ratio calculation
    mock_history = {
        fixed_today - timedelta(days=2): Decimal("95.0"),
        fixed_today - timedelta(days=1): Decimal("105.0"),
        fixed_today: Decimal("110.0"),
    }
    mocker.patch.object(financial_data_service, "get_historical_prices", return_value={"CALC1": mock_history})

    # 5. Make the request
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/analytics",
        headers=auth_headers,
    )

    # 6. Assertions
    assert response.status_code == 200
    data = response.json()

    # Expected XIRR for buying at 100 and current value being 110 after 1 year is ~10%
    assert "xirr" in data
    assert data["xirr"] == pytest.approx(0.10, abs=1e-2)

    # Assert Sharpe Ratio is calculated and is a float
    assert "sharpe_ratio" in data
    assert isinstance(data["sharpe_ratio"], float)
    assert data["sharpe_ratio"] != 0.0


def test_get_asset_analytics_success(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """
    Test successful retrieval of asset analytics (basic case).
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(email=user.email, password=password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Asset Analytics Portfolio")
    transaction = create_test_transaction(
        db, portfolio_id=portfolio.id, ticker="ASSET1", quantity=10
    )
    asset_id = transaction.asset_id

    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/assets/{asset_id}/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "realized_xirr" in content
    assert "unrealized_xirr" in content


def test_get_asset_analytics_no_transactions(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """
    Test that 0.0 is returned for an asset with no transactions.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(email=user.email, password=password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Asset Analytics Portfolio")
    asset = create_test_asset(db, ticker_symbol="EMPTY")
    
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/assets/{asset.id}/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["realized_xirr"] == 0.0
    assert content["unrealized_xirr"] == 0.0


def test_get_asset_analytics_forbidden(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """
    Test that a 403 is returned when trying to access another user's asset analytics.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(email=user.email, password=password)

    other_user, _ = create_random_user(db)
    other_portfolio = create_test_portfolio(db, user_id=other_user.id, name="Other User Portfolio")
    other_transaction = create_test_transaction(
        db, portfolio_id=other_portfolio.id, ticker="OTHER", quantity=10
    )
    other_asset_id = other_transaction.asset_id

    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{other_portfolio.id}/assets/{other_asset_id}/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_get_asset_analytics_calculation_realized_and_unrealized(
    client: TestClient, db: Session, get_auth_headers, mocker
) -> None:
    """
    Test the realized and unrealized XIRR calculation with a mix of buys and sells.
    """
    fixed_today = date(2024, 8, 1)
    mocker.patch("app.crud.crud_analytics.date").today.return_value = fixed_today

    user, password = create_random_user(db)
    auth_headers = get_auth_headers(email=user.email, password=password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="XIRR Calc Portfolio")

    buy_tx = create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="XIRR_TEST",
        quantity=Decimal(10),
        price_per_unit=Decimal(100),
        transaction_type="BUY",
        transaction_date=fixed_today - timedelta(days=365),
    )
    asset_id = buy_tx.asset_id

    create_test_transaction(
        db,
        portfolio_id=portfolio.id, # The helper finds the asset by ticker
        ticker="XIRR_TEST",
        quantity=Decimal(5),
        price_per_unit=Decimal(120),
        transaction_type="SELL",
        transaction_date=fixed_today - timedelta(days=182),
    )

    mock_prices = {"XIRR_TEST": {"current_price": Decimal("130.0"), "previous_close": Decimal("129.0")}}
    mocker.patch.object(financial_data_service, "get_current_prices", return_value=mock_prices)

    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/assets/{asset_id}/analytics",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # The correct annualized return for a 20% gain over 183 days is ~0.4386
    assert data["realized_xirr"] == pytest.approx(0.4386, abs=1e-4)
    assert data["unrealized_xirr"] == pytest.approx(0.3000, abs=1e-4)
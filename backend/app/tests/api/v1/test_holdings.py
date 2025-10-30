from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.financial_data_service import financial_data_service
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_get_portfolio_summary_and_holdings_success(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    # 1. Setup
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Holdings Test")

    # Create transactions to establish a known state
    # Asset 1: Buy 10 @ 100, Sell 5 @ 120
    # Expected holding: 5 shares, avg_buy_price=100, total_invested=500
    # Expected realized PNL: (120 - 100) * 5 = 100
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="ASSET1",
        transaction_type="BUY",
        quantity=10,
        price_per_unit=100,
    )
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="ASSET1",
        transaction_type="SELL",
        quantity=5,
        price_per_unit=120,
    )

    # Asset 2: Buy 20 @ 50
    # Expected holding: 20 shares, avg_buy_price=50, total_invested=1000
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="ASSET2",
        transaction_type="BUY",
        quantity=20,
        price_per_unit=50,
    )

    # Mock the external financial data service
    mock_prices = {
        "ASSET1": {
            "current_price": Decimal("150.0"),
            "previous_close": Decimal("140.0"),
        },
        "ASSET2": {"current_price": Decimal("45.0"), "previous_close": Decimal("48.0")},
    }
    mocker.patch.object(
        financial_data_service, "get_current_prices", return_value=mock_prices
    )

    # 2. Test Summary Endpoint
    summary_response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/summary", headers=headers
    )
    assert summary_response.status_code == 200
    summary_data = summary_response.json()

    # Expected calculations for summary
    # Total Value = (5 * 150) + (20 * 45) = 750 + 900 = 1650
    # Total Invested = 500 (ASSET1) + 1000 (ASSET2) = 1500
    # Day's PNL = (150-140)*5 + (45-48)*20 = 50 - 60 = -10
    # Unrealized PNL = 1650 - 1500 = 150
    # Realized PNL = 100
    assert Decimal(summary_data["total_value"]) == Decimal("1650.0")
    assert Decimal(summary_data["total_invested_amount"]) == Decimal("1500.0")
    assert Decimal(summary_data["days_pnl"]) == Decimal("-10.0")
    assert Decimal(summary_data["total_unrealized_pnl"]) == Decimal("150.0")
    assert Decimal(summary_data["total_realized_pnl"]) == Decimal("100.0")

    # 3. Test Holdings Endpoint
    holdings_response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/holdings", headers=headers
    )
    assert holdings_response.status_code == 200
    holdings_data = holdings_response.json()["holdings"]

    assert len(holdings_data) == 2

    asset1_holding = next(
        (h for h in holdings_data if h["ticker_symbol"] == "ASSET1"), None
    )
    asset2_holding = next(
        (h for h in holdings_data if h["ticker_symbol"] == "ASSET2"), None
    )

    assert asset1_holding is not None
    assert asset2_holding is not None

    # Assertions for ASSET1
    assert Decimal(asset1_holding["quantity"]) == Decimal("5")
    assert Decimal(asset1_holding["average_buy_price"]) == Decimal("100.0")
    assert Decimal(asset1_holding["current_value"]) == Decimal("750.0")  # 5 * 150
    assert Decimal(asset1_holding["unrealized_pnl"]) == Decimal("250.0")  # 750 - 500

    # Assertions for ASSET2
    assert Decimal(asset2_holding["quantity"]) == Decimal("20")
    assert Decimal(asset2_holding["average_buy_price"]) == Decimal("50.0")
    assert Decimal(asset2_holding["current_value"]) == Decimal("900.0")  # 20 * 45
    assert Decimal(asset2_holding["unrealized_pnl"]) == Decimal("-100.0")  # 900 - 1000


def test_get_portfolio_summary_and_holdings_empty(
    client: TestClient, db: Session, get_auth_headers
):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Empty Portfolio")

    # Test Summary
    summary_response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/summary", headers=headers
    )
    assert summary_response.status_code == 200
    summary_data = summary_response.json()
    for key, value in summary_data.items():
        assert Decimal(value) == Decimal(0)

    # Test Holdings
    holdings_response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/holdings", headers=headers
    )
    assert holdings_response.status_code == 200
    assert holdings_response.json()["holdings"] == []


def test_get_portfolio_summary_wrong_owner(
    client: TestClient, db: Session, get_auth_headers
):
    user1, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user1.id, name="User1 Portfolio")

    user2, password2 = create_random_user(db)
    headers2 = get_auth_headers(user2.email, password2)

    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/summary", headers=headers2
    )
    assert response.status_code == 403


def test_get_portfolio_holdings_wrong_owner(
    client: TestClient, db: Session, get_auth_headers
):
    user1, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user1.id, name="User1 Portfolio")

    user2, password2 = create_random_user(db)
    headers2 = get_auth_headers(user2.email, password2)

    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/holdings", headers=headers2
    )
    assert response.status_code == 403


def test_summary_with_dividend(
    client: TestClient, db: Session, get_auth_headers, mocker
) -> None:
    """
    Test portfolio summary calculation with a dividend transaction.
    This test is expected to fail until FR6.2 is implemented.
    """
    # 1. Setup
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(
        db, user_id=user.id, name="Summary Test Portfolio"
    )

    # 2. Transactions
    # Buy 10 shares at 100
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="RELIANCE",
        transaction_type="BUY",
        quantity=10,
        price_per_unit=100,
        transaction_date=date(2023, 1, 1),
    )
    # Receive a dividend of 100
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="RELIANCE",
        transaction_type="DIVIDEND",
        quantity=100,
        price_per_unit=1,
        transaction_date=date(2023, 7, 1),
    )

    # 3. Mock current price
    # Current price is 110 per share. Current value of holding is 1100.
    mock_prices = {
        "RELIANCE": {"current_price": Decimal("110"), "previous_close": Decimal("108")}
    }
    mocker.patch.object(
        financial_data_service, "get_current_prices", return_value=mock_prices
    )

    # 4. API Call
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/summary",
        headers=auth_headers,
    )
    data = response.json()

    # 5. Assertions
    assert response.status_code == 200
    # Expected: Realized PNL should be the dividend amount (100).
    assert Decimal(data["total_realized_pnl"]) == pytest.approx(Decimal("100.0"))
    # Expected: Total value should be current holding value (1100)
    assert Decimal(data["total_value"]) == pytest.approx(Decimal("1100.0"))


def test_summary_with_mf_dividend(
    client: TestClient, db: Session, get_auth_headers, mocker
) -> None:
    """
    Test portfolio summary calculation with a Mutual Fund dividend transaction.
    This test validates FR4.5.1.
    """
    # 1. Setup
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(
        db, user_id=user.id, name="MF Dividend Test Portfolio"
    )

    # 2. Transactions
    # Buy 100 units of a mutual fund
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="120503",  # HDFC Index Fund
        asset_type="Mutual Fund",
        transaction_type="BUY",
        quantity=100,
        price_per_unit=500,
        transaction_date=date(2023, 1, 1),
    )
    # Receive a dividend of 2500
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="120503",
        asset_type="Mutual Fund",
        transaction_type="DIVIDEND",
        quantity=2500, # Total dividend amount
        price_per_unit=1,
        transaction_date=date(2023, 7, 1),
    )

    # 3. Mock current price (not relevant for realized P&L)
    mocker.patch.object(financial_data_service, "get_current_prices", return_value={})

    # 4. API Call
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/summary",
        headers=auth_headers,
    )
    data = response.json()

    # 5. Assertions
    assert response.status_code == 200
    # Expected: Realized PNL should be the dividend amount (2500).
    assert Decimal(data["total_realized_pnl"]) == pytest.approx(Decimal("2500.0"))

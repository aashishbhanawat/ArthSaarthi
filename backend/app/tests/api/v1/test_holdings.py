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


def test_rsu_vest_with_sell_to_cover_holdings(
    client: TestClient, db: Session, get_auth_headers, mocker
) -> None:
    """
    Test that RSU_VEST with sell-to-cover correctly calculates average buy
    price and unrealized P&L using FMV as cost basis (not $0 price_per_unit).

    Regression test for Issue #249.
    """
    from datetime import datetime

    from app.tests.utils.asset import create_test_asset

    # 1. Setup
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(
        db, user_id=user.id, name="RSU Holdings Test"
    )
    asset = create_test_asset(db, ticker_symbol="CSCO")

    # 2. Create RSU_VEST: 100 shares, FMV=$70, FX=85, sell-to-cover 40@70
    rsu_payload = {
        "asset_id": str(asset.id),
        "transaction_type": "RSU_VEST",
        "quantity": 100,
        "price_per_unit": 0,
        "transaction_date": datetime(2025, 1, 1).isoformat(),
        "details": {
            "fmv": 70.0,
            "fx_rate": 85.0,
            "sell_to_cover": {
                "quantity": 40,
                "price_per_unit": 70.0,
            },
        },
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/"
        f"?portfolio_id={portfolio.id}",
        headers=headers,
        json=rsu_payload,
    )
    assert response.status_code == 201, response.text

    # 3. Mock: stock prices (call 1), FX rates (call 2)
    stock_prices = {
        "CSCO": {
            "current_price": Decimal("78.0"),
            "previous_close": Decimal("77.0"),
        },
    }
    fx_prices = {
        "USDINR=X": {
            "current_price": Decimal("85.0"),
            "previous_close": Decimal("85.0"),
        },
    }
    mocker.patch.object(
        financial_data_service,
        "get_current_prices",
        side_effect=[stock_prices, fx_prices],
    )

    # 4. Get holdings
    holdings_response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/holdings",
        headers=headers,
    )
    assert holdings_response.status_code == 200
    holdings_data = holdings_response.json()["holdings"]

    csco = next(
        (h for h in holdings_data if h["ticker_symbol"] == "CSCO"),
        None,
    )
    assert csco is not None

    # 5. Assertions
    # Remaining: 100 - 40 = 60
    assert Decimal(csco["quantity"]) == Decimal("60")

    # avg_buy_price = FMV * FX = 70 * 85 = 5950 INR
    avg = Decimal(csco["average_buy_price"])
    assert avg == pytest.approx(Decimal("5950.0"), abs=Decimal("1"))

    # total_invested = 60 * 70 * 85 = 357,000
    invested = Decimal(csco["total_invested_amount"])
    assert invested == pytest.approx(
        Decimal("357000.0"), abs=Decimal("1")
    )

    # current_value = 60 * 78 * 85 = 397,800
    # unrealized = 397800 - 357000 = 40,800 (positive)
    pnl = Decimal(csco["unrealized_pnl"])
    assert pnl > 0, f"Unrealized P&L should be positive, got {pnl}"


def test_rsu_vest_plain_holdings(
    client: TestClient, db: Session, get_auth_headers, mocker
) -> None:
    """
    Test that a plain RSU_VEST (without sell-to-cover) correctly uses FMV
    as cost basis in holdings calculations.
    """
    from datetime import datetime

    from app.tests.utils.asset import create_test_asset

    # 1. Setup
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(
        db, user_id=user.id, name="RSU Plain Test"
    )
    asset = create_test_asset(db, ticker_symbol="MSFT")

    # 2. RSU_VEST: 50 shares, FMV=$100, FX=83.5, no sell-to-cover
    rsu_payload = {
        "asset_id": str(asset.id),
        "transaction_type": "RSU_VEST",
        "quantity": 50,
        "price_per_unit": 0,
        "transaction_date": datetime(2025, 1, 1).isoformat(),
        "details": {
            "fmv": 100.0,
            "fx_rate": 83.5,
        },
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/"
        f"?portfolio_id={portfolio.id}",
        headers=headers,
        json=rsu_payload,
    )
    assert response.status_code == 201, response.text

    # 3. Mock: stock prices (call 1), FX rates (call 2)
    stock_prices = {
        "MSFT": {
            "current_price": Decimal("110.0"),
            "previous_close": Decimal("108.0"),
        },
    }
    fx_prices = {
        "USDINR=X": {
            "current_price": Decimal("83.5"),
            "previous_close": Decimal("83.5"),
        },
    }
    mocker.patch.object(
        financial_data_service,
        "get_current_prices",
        side_effect=[stock_prices, fx_prices],
    )

    # 4. Get holdings
    holdings_response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/holdings",
        headers=headers,
    )
    assert holdings_response.status_code == 200
    holdings_data = holdings_response.json()["holdings"]

    msft = next(
        (h for h in holdings_data if h["ticker_symbol"] == "MSFT"),
        None,
    )
    assert msft is not None

    # 5. Assertions
    assert Decimal(msft["quantity"]) == Decimal("50")

    # avg = FMV * FX = 100 * 83.5 = 8350
    avg = Decimal(msft["average_buy_price"])
    assert avg == pytest.approx(Decimal("8350.0"), abs=Decimal("1"))

    # current_value = 50 * 110 * 83.5 = 458,250
    # total_invested = 50 * 100 * 83.5 = 417,500
    # unrealized = 458250 - 417500 = 40,750 (positive)
    pnl = Decimal(msft["unrealized_pnl"])
    assert pnl > 0, f"Unrealized P&L should be positive, got {pnl}"

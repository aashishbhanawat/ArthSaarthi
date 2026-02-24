from datetime import date, timedelta
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


def test_get_dashboard_summary_unauthorized(client: TestClient):
    """Test that an unauthenticated user receives a 401 Unauthorized error."""
    response = client.get(f"{settings.API_V1_STR}/dashboard/summary")
    assert response.status_code == 401


def test_get_dashboard_summary_no_portfolios(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    """
    Test that a user with no portfolios receives an empty summary.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    response = client.get(
        f"{settings.API_V1_STR}/dashboard/summary", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_value"] == "0.0"
    assert data["total_unrealized_pnl"] == "0.0"
    assert data["total_realized_pnl"] == "0.0"
    assert data["top_movers"] == []
    assert data["asset_allocation"] == []


def test_get_dashboard_summary_success(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    """Test successful retrieval and calculation of a dashboard summary."""
    # 1. Setup User and Auth
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="P&L Test Portfolio")

    # 2. Create a more complex transaction history to test P/L
    # Scenario:
    # - Buy 10 AAPL @ $100
    # - Buy 10 AAPL @ $120 -> Avg cost is now $110
    # - Sell 5 AAPL @ $130 -> Realized P/L = 5 * (130 - 110) = $100
    # - Buy 2 GOOG @ $2500
    # Current holdings: 15 AAPL, 2 GOOG
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="AAPL",
        quantity=10,
        price_per_unit=100,
        transaction_type="BUY",
        transaction_date=date(2023, 1, 1),
    )
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="AAPL",
        quantity=10,
        price_per_unit=120,
        transaction_type="BUY",
        transaction_date=date(2023, 1, 2),
    )
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="AAPL",
        quantity=5,
        price_per_unit=130,
        transaction_type="SELL",
        transaction_date=date(2023, 1, 3),
    )
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="GOOG",
        quantity=2,
        price_per_unit=2500,
        transaction_type="BUY",
        transaction_date=date(2023, 1, 4),
    )

    # 3. Mock financial data service for current prices
    mock_prices = {
        "AAPL": {"current_price": Decimal("150.0"), "previous_close": Decimal("145.0")},
        "GOOG": {
            "current_price": Decimal("2800.0"),
            "previous_close": Decimal("2750.0"),
        },
    }
    mocker.patch.object(
        financial_data_service, "get_current_prices", return_value=mock_prices
    )

    # 4. Make API call
    response = client.get(
        f"{settings.API_V1_STR}/dashboard/summary", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # 5. Assertions
    # Total Value = (15 AAPL * 150) + (2 GOOG * 2800) = 2250 + 5600 = 7850
    assert Decimal(data["total_value"]).quantize(Decimal("0.01")) == Decimal("7850.00")

    # Unrealized P/L calculation (FIFO):
    # AAPL:
    #   Sell 5 consumed 5 from Jan 1 (Buy @ 100).
    #   Remaining: 5 @ 100, 10 @ 120. Total 15.
    #   Cost Basis = (5 * 100) + (10 * 120) = 500 + 1200 = 1700.
    #   Current Value = 15 * 150 = 2250.
    #   Unrealized P/L = 2250 - 1700 = 550.
    # GOOG:
    #   Unrealized P/L = (2800 - 2500) * 2 = 600.
    # Total Unrealized P/L = 550 + 600 = 1150.
    assert Decimal(data["total_unrealized_pnl"]).quantize(Decimal("0.01")) == Decimal(
        "1150.00"
    )

    # Realized P/L calculation (FIFO):
    # Sell 5 @ 130.
    # Cost Basis (FIFO) = 5 @ 100 = 500.
    # Proceeds = 5 * 130 = 650.
    # Realized PnL = 650 - 500 = 150.
    assert Decimal(data["total_realized_pnl"]).quantize(Decimal("0.01")) == Decimal(
        "150.00"
    )

    assert len(data["asset_allocation"]) == 2
    assert len(data["top_movers"]) == 2
    aapl_mover = next(m for m in data["top_movers"] if m["ticker_symbol"] == "AAPL")
    assert Decimal(aapl_mover["daily_change"]) == Decimal("5.0")


def test_get_dashboard_summary_with_failing_price_lookup(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    """Test that the summary calculation handles assets where price lookup fails."""
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    mocker.patch.object(financial_data_service, "get_current_prices", return_value={})

    portfolio = create_test_portfolio(db, user_id=user.id, name="Failing Portfolio")
    create_test_transaction(
        db, portfolio_id=portfolio.id, ticker="FAIL", quantity=10, asset_type="Stock"
    )

    response = client.get(
        f"{settings.API_V1_STR}/dashboard/summary", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # For stocks, if price lookup fails, the value is 0. The fallback to book
    # value only applies to non-market-traded assets like bonds.
    assert Decimal(data["total_value"]).quantize(Decimal("0.01")) == Decimal("0.00")
    # Unrealized P&L = current_value (0) - total_invested (1000) = -1000
    assert Decimal(data["total_unrealized_pnl"]).quantize(Decimal("0.01")) == Decimal(
        "-1000.00"
    )


# --- Tests for /allocation endpoint ---


def test_get_asset_allocation_unauthorized(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/dashboard/allocation")
    assert response.status_code == 401


def test_get_asset_allocation_success(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    create_test_transaction(
        db, portfolio_id=portfolio.id, ticker="TSLA", quantity=10, asset_type="Stock"
    )
    create_test_transaction(
        db, portfolio_id=portfolio.id, ticker="MSFT", quantity=5, asset_type="Stock"
    )

    mock_prices = {
        "TSLA": {"current_price": Decimal("200.0"), "previous_close": Decimal("190.0")},
        "MSFT": {"current_price": Decimal("300.0"), "previous_close": Decimal("295.0")},
    }
    mocker.patch.object(
        financial_data_service, "get_current_prices", return_value=mock_prices
    )

    response = client.get(
        f"{settings.API_V1_STR}/dashboard/allocation", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert "allocation" in data
    assert len(data["allocation"]) == 2
    allocation_map = {
        item["ticker"]: Decimal(item["value"]) for item in data["allocation"]
    }
    assert allocation_map["TSLA"] == Decimal("2000.0")  # 10 * 200
    assert allocation_map["MSFT"] == Decimal("1500.0")  # 5 * 300


# --- Tests for /history endpoint ---


def test_get_portfolio_history_unauthorized(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/dashboard/history")
    assert response.status_code == 401


def test_get_portfolio_history_success(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="History Portfolio")

    today = date.today()
    # Transaction outside the 7d range, to test initial holdings calculation
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="NVDA",
        quantity=10,
        asset_type="Stock",
        transaction_date=today - timedelta(days=10),
    )
    # Transaction inside the 7d range
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="NVDA",
        quantity=5,
        asset_type="Stock",
        transaction_date=today - timedelta(days=5),
    )

    mock_history = {}
    for i in range(8):
        d = today - timedelta(days=i)
        mock_history[d] = Decimal("500.0")

    mocker.patch.object(
        financial_data_service,
        "get_historical_prices",
        return_value={"NVDA": mock_history},
    )

    response = client.get(
        f"{settings.API_V1_STR}/dashboard/history?range=7d", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert "history" in data
    history = data["history"]
    # 7 days ago up to today inclusive = 8 points
    assert len(history) == 8

    # Value for first 2 days of window (days -7, -6) should be 5000 (10 shares * 500)
    assert Decimal(history[1]["value"]) == Decimal("5000.0")
    # Value should jump to 7500 on day -5 (15 shares * 500)
    assert Decimal(history[2]["value"]) == Decimal("7500.0")
    assert Decimal(history[7]["value"]) == Decimal("7500.0")  # Today


def test_portfolio_xirr_with_dividend(
    client: TestClient, db: Session, get_auth_headers, mocker
) -> None:
    """
    Test that the portfolio-level XIRR calculation correctly includes dividends as a
    positive cash flow.
    This test is expected to fail until FR6.2 is implemented.

    Cash Flow Calculation:
    - 2023-01-01: -1000 (Outflow for BUY 10 shares @ 100)
    - 2023-07-01: +100  (Inflow from DIVIDEND)
    - 2024-01-01: +1100 (Terminal value of holding: 10 shares * 110 current price)

    Using an online XIRR calculator with these values gives an expected result of
    ~21.7%.
    """
    # 1. Mock date.today() for a predictable calculation window
    fixed_today = date(2024, 1, 1)
    mocker.patch("app.crud.crud_analytics.date").today.return_value = fixed_today

    # 2. Setup
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="XIRR Dividend Test")

    # 3. Transactions
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="RELIANCE",
        transaction_type="BUY",
        quantity=10,
        price_per_unit=100,
        transaction_date=date(2023, 1, 1),
    )
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="RELIANCE",
        transaction_type="DIVIDEND",
        quantity=100,
        price_per_unit=1,
        transaction_date=date(2023, 7, 1),
    )

    # 4. Mock financial data
    mock_prices = {
        "RELIANCE": {"current_price": Decimal("110"), "previous_close": Decimal("108")}
    }
    mocker.patch.object(
        financial_data_service, "get_current_prices", return_value=mock_prices
    )
    mocker.patch.object(
        financial_data_service, "get_historical_prices", return_value={}
    )

    # 5. API Call
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/analytics",
        headers=auth_headers,
    )
    data = response.json()

    # 6. Assertion
    assert response.status_code == 200
    # The current logic ignores the dividend, calculating XIRR for a simple 10% gain
    # over 1 year, which is 0.10.
    # The correct XIRR, including the dividend, should be ~21.7%.
    # After implementation, the correct XIRR for this cash flow is ~21.0%.
    assert data["xirr"] == pytest.approx(0.210, abs=0.001)

def test_get_portfolio_history_with_snapshots(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    from app.models.portfolio_snapshot import DailyPortfolioSnapshot
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Snapshot History")

    today = date.today()
    yesterday = today - timedelta(days=1)
    snapshot = DailyPortfolioSnapshot(
        portfolio_id=portfolio.id,
        snapshot_date=yesterday,
        total_value=Decimal("9999.99"),
        equity_value=Decimal("9999.99")
    )
    db.add(snapshot)
    db.commit()

    # We also need a transaction so that the history endpoint even bothers retrieving
    # assets
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="NVDA",
        quantity=1,
        asset_type="Stock",
        transaction_date=today - timedelta(days=2),
    )

    mocker.patch.object(
        financial_data_service,
        "get_historical_prices",
        return_value={
            "NVDA": {
                today: Decimal("100.0"),
                today - timedelta(days=1): Decimal("100.0"),
            }
        },
    )

    response = client.get(
        f"{settings.API_V1_STR}/dashboard/history?range=7d", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert "history" in data

    # Yesterday's history entry should use the 9999.99 snapshot value
    yesterday_entry = next(
        (i for i in data["history"] if i["date"] == yesterday.isoformat()), None
    )
    assert yesterday_entry is not None
    assert Decimal(yesterday_entry["value"]).quantize(Decimal("0.01")) == Decimal(
        "9999.99"
    )

    # Today's history entry should use live calculation (100.0)
    today_entry = next(
        (i for i in data["history"] if i["date"] == today.isoformat()), None
    )
    assert today_entry is not None
    assert Decimal(today_entry["value"]).quantize(Decimal("0.01")) == Decimal("100.00")


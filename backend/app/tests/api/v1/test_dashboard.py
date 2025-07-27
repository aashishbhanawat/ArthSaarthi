from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
from decimal import Decimal

from app.core.config import settings
from app.tests.utils.user import create_random_user
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.services.financial_data_service import financial_data_service


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
    response = client.get(f"{settings.API_V1_STR}/dashboard/summary", headers=auth_headers)
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
    create_test_transaction(db, portfolio_id=portfolio.id, ticker="AAPL", quantity=10, price_per_unit=100, transaction_type="BUY", transaction_date=date(2023, 1, 1))
    create_test_transaction(db, portfolio_id=portfolio.id, ticker="AAPL", quantity=10, price_per_unit=120, transaction_type="BUY", transaction_date=date(2023, 1, 2))
    create_test_transaction(db, portfolio_id=portfolio.id, ticker="AAPL", quantity=5, price_per_unit=130, transaction_type="SELL", transaction_date=date(2023, 1, 3))
    create_test_transaction(db, portfolio_id=portfolio.id, ticker="GOOG", quantity=2, price_per_unit=2500, transaction_type="BUY", transaction_date=date(2023, 1, 4))

    # 3. Mock financial data service for current prices
    mock_prices = {
        "AAPL": {"current_price": Decimal("150.0"), "previous_close": Decimal("145.0")},
        "GOOG": {"current_price": Decimal("2800.0"), "previous_close": Decimal("2750.0")},
    }
    mocker.patch.object(financial_data_service, "get_current_prices", return_value=mock_prices)

    # 4. Make API call
    response = client.get(f"{settings.API_V1_STR}/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # 5. Assertions
    # Total Value = (15 AAPL * 150) + (2 GOOG * 2800) = 2250 + 5600 = 7850
    assert Decimal(data["total_value"]).quantize(Decimal("0.01")) == Decimal("7850.00")

    # Unrealized P/L for AAPL = (150 - 110) * 15 = 600
    # Unrealized P/L for GOOG = (2800 - 2500) * 2 = 600
    # Total Unrealized P/L = 600 + 600 = 1200
    assert Decimal(data["total_unrealized_pnl"]).quantize(Decimal("0.01")) == Decimal("1200.00")

    # Realized P/L was calculated in the scenario above as 100
    assert Decimal(data["total_realized_pnl"]).quantize(Decimal("0.01")) == Decimal("100.00")

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
    create_test_transaction(db, portfolio_id=portfolio.id, ticker="FAIL", quantity=10, asset_type="Stock")

    response = client.get(f"{settings.API_V1_STR}/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # The failing asset should be valued at 0
    assert Decimal(data["total_value"]) == Decimal("0.0")


# --- Tests for /allocation endpoint ---

def test_get_asset_allocation_unauthorized(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/dashboard/allocation")
    assert response.status_code == 401


def test_get_asset_allocation_success(client: TestClient, db: Session, get_auth_headers, mocker):
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    create_test_transaction(db, portfolio_id=portfolio.id, ticker="TSLA", quantity=10, asset_type="Stock")
    create_test_transaction(db, portfolio_id=portfolio.id, ticker="MSFT", quantity=5, asset_type="Stock")

    mock_prices = {
        "TSLA": {"current_price": Decimal("200.0"), "previous_close": Decimal("190.0")},
        "MSFT": {"current_price": Decimal("300.0"), "previous_close": Decimal("295.0")},
    }
    mocker.patch.object(financial_data_service, "get_current_prices", return_value=mock_prices)

    response = client.get(f"{settings.API_V1_STR}/dashboard/allocation", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "allocation" in data
    assert len(data["allocation"]) == 2
    allocation_map = {item["ticker"]: Decimal(item["value"]) for item in data["allocation"]}
    assert allocation_map["TSLA"] == Decimal("2000.0") # 10 * 200
    assert allocation_map["MSFT"] == Decimal("1500.0") # 5 * 300


# --- Tests for /history endpoint ---

def test_get_portfolio_history_unauthorized(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/dashboard/history")
    assert response.status_code == 401


def test_get_portfolio_history_success(client: TestClient, db: Session, get_auth_headers, mocker):
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="History Portfolio")

    today = date.today()
    # Transaction outside the 7d range, to test initial holdings calculation
    create_test_transaction(db, portfolio_id=portfolio.id, ticker="NVDA", quantity=10, asset_type="Stock", transaction_date=today - timedelta(days=10))
    # Transaction inside the 7d range
    create_test_transaction(db, portfolio_id=portfolio.id, ticker="NVDA", quantity=5, asset_type="Stock", transaction_date=today - timedelta(days=5))

    mock_history = {}
    for i in range(8):
        d = today - timedelta(days=i)
        mock_history[d] = Decimal("500.0")

    mocker.patch.object(financial_data_service, "get_historical_prices", return_value={"NVDA": mock_history})

    response = client.get(f"{settings.API_V1_STR}/dashboard/history?range=7d", headers=auth_headers)
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
    assert Decimal(history[7]["value"]) == Decimal("7500.0") # Today
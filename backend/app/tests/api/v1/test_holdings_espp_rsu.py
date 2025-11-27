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

def test_get_portfolio_holdings_with_rsu_and_espp(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    # 1. Setup
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="RSU/ESPP Test")

    # 2. Transactions

    # RSU Vest: 10 units @ 0
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="GOOGL",
        transaction_type="RSU_VEST",
        quantity=10,
        price_per_unit=0,
        details={"fmv_at_vest": 150.0, "exchange_rate_to_inr": 1.0},
    )

    # Sell to Cover: 4 units @ 100
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="GOOGL",
        transaction_type="SELL",
        quantity=4,
        price_per_unit=100,
    )

    # ESPP Purchase: 20 units @ 85
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="MSFT",
        transaction_type="ESPP_PURCHASE",
        quantity=20,
        price_per_unit=85,
        details={"market_price": 100.0, "exchange_rate_to_inr": 1.0},
    )

    # Mock prices
    mock_prices = {
        "GOOGL": {"current_price": Decimal("110.0"), "previous_close": Decimal("100.0")},
        "MSFT": {"current_price": Decimal("100.0"), "previous_close": Decimal("90.0")},
    }
    mocker.patch.object(
        financial_data_service, "get_current_prices", return_value=mock_prices
    )

    # 3. Test Holdings Endpoint
    holdings_response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/holdings", headers=headers
    )
    assert holdings_response.status_code == 200
    holdings_data = holdings_response.json()["holdings"]

    assert len(holdings_data) == 2

    googl = next((h for h in holdings_data if h["ticker_symbol"] == "GOOGL"), None)
    msft = next((h for h in holdings_data if h["ticker_symbol"] == "MSFT"), None)

    assert googl is not None
    assert msft is not None

    # Check GOOGL
    # Qty: 10 - 4 = 6
    assert Decimal(googl["quantity"]) == Decimal("6")
    # Cost Basis: 0 (RSU has 0 cost) - 0 (sold part has 0 cost) = 0?
    # RSU 10 @ 0 -> Total Invested 0.
    # Sell 4. Proportion 4/10 = 0.4. Invested reduced by 40% -> 0.
    # Avg price = 0 / 6 = 0.
    assert Decimal(googl["average_buy_price"]) == Decimal("0.0")
    assert Decimal(googl["total_invested_amount"]) == Decimal("0.0")

    # Check MSFT
    # Qty: 20
    assert Decimal(msft["quantity"]) == Decimal("20")
    # Cost Basis: 20 * 85 = 1700
    assert Decimal(msft["total_invested_amount"]) == Decimal("1700.0")

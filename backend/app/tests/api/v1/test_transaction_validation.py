from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_sell_transaction_before_buy_date_fails(
    client: TestClient, db: Session, get_auth_headers
):
    """Test selling an asset before its purchase date fails."""
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(
        db, user_id=user.id, name="Validation Test Portfolio"
    )

    # 1. Buy GOOGL on a specific date
    buy_date = date(2024, 11, 6)
    buy_transaction = create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="GOOGL",
        quantity=10,
        price_per_unit=100,
        asset_type="Stock",
        transaction_date=buy_date,
        fees=0.0,
    )
    asset_id = buy_transaction.asset_id

    # 2. Attempt to sell GOOGL *before* the buy date
    sell_date = date(2024, 1, 2)
    sell_transaction_data = {
        "ticker_symbol": "GOOGL",
        "asset_type": "Stock",
        "transaction_type": "SELL",
        "quantity": 5,
        "price_per_unit": 3000,
        "transaction_date": sell_date.isoformat(),
    }

    response = client.post(
        f"{settings.API_V1_STR}/transactions/?portfolio_id={portfolio.id}",
        headers=auth_headers,
        json=sell_transaction_data,
    )

    # 3. Assert that the API returns a 400 Bad Request with the correct error
    assert response.status_code == 400
    data = response.json()
    assert "Insufficient holdings to sell" in data["detail"]
    assert "Current holdings: 0" in data["detail"]

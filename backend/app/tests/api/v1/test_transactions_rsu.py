import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Callable, Dict
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")

def test_create_rsu_with_sell_to_cover(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    user_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="RSU Portfolio")
    asset = create_test_asset(db, ticker_symbol="GOOGL")

    payload = {
        "asset_id": str(asset.id),
        "transaction_type": "RSU_VEST",
        "quantity": 10,
        "price_per_unit": 0,
        "transaction_date": datetime.now().isoformat(),
        "details": {
            "sell_to_cover": {
                "quantity": 4,
                "price_per_unit": 150.0
            }
        }
    }

    response = client.post(
        f"{settings.API_V1_STR}/transactions/?portfolio_id={portfolio.id}",
        headers=user_headers,
        json=payload
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert "created_transactions" in data
    txs = data["created_transactions"]
    assert len(txs) == 2

    rsu_tx = next(tx for tx in txs if tx["transaction_type"] == "RSU_VEST")
    sell_tx = next(tx for tx in txs if tx["transaction_type"] == "SELL")

    # Compare as floats or strings
    assert float(rsu_tx["quantity"]) == 10.0
    assert float(sell_tx["quantity"]) == 4.0
    assert float(sell_tx["price_per_unit"]) == 150.0

def test_get_fx_rate(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    user_headers = get_auth_headers(user.email, password)

    date_str = date.today().isoformat()
    response = client.get(
        f"{settings.API_V1_STR}/fx-rate/?from=USD&to=INR&date={date_str}",
        headers=user_headers
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "rate" in data
    assert float(data["rate"]) == 83.50

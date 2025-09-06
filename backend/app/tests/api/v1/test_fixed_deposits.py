from datetime import date, timedelta
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_create_fixed_deposit(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    headers = get_auth_headers(user.email, password)
    data = {
        "name": "Test FD",
        "principal_amount": 10000.0,
        "interest_rate": 5.0,
        "start_date": (date.today() - timedelta(days=365)).isoformat(),
        "maturity_date": (date.today() + timedelta(days=365 * 4)).isoformat(),
        "compounding_frequency": "Annually",
        "interest_payout": "Cumulative",
        "account_number": "1234567890"
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/fixed-deposits/",
        json=data,
        headers=headers,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["name"] == data["name"]
    assert float(content["principal_amount"]) == data["principal_amount"]
    assert float(content["interest_rate"]) == data["interest_rate"]
    assert content["start_date"] == data["start_date"]
    assert content["maturity_date"] == data["maturity_date"]
    assert content["compounding_frequency"] == data["compounding_frequency"]
    assert content["interest_payout"] == data["interest_payout"]
    assert content["account_number"] == data["account_number"]
    assert "id" in content
    assert "portfolio_id" in content
    assert "user_id" in content


def test_read_fixed_deposit_with_analytics(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    headers = get_auth_headers(user.email, password)
    data = {
        "name": "Test FD",
        "principal_amount": 10000.0,
        "interest_rate": 5.0,
        "start_date": (date.today() - timedelta(days=365)).isoformat(),
        "maturity_date": (date.today() + timedelta(days=365 * 4)).isoformat(),
        "compounding_frequency": "Annually",
        "interest_payout": "Cumulative",
        "account_number": "1234567890"
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/fixed-deposits/",
        json=data,
        headers=headers,
    )
    fd_id = response.json()["id"]

    # Test the details endpoint first
    response = client.get(
        f"{settings.API_V1_STR}/fixed-deposits/{fd_id}",
        headers=headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "maturity_value" in content
    assert float(content["maturity_value"]) > data["principal_amount"]

    # Test the analytics endpoint
    response = client.get(
        f"{settings.API_V1_STR}/fixed-deposits/{fd_id}/analytics",
        headers=headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "unrealized_xirr" in content
    assert "realized_xirr" in content

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user, get_access_token


def test_create_fixed_deposit(client: TestClient, db: Session) -> None:
    user, password = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    access_token = get_access_token(client, user.email, password)
    data = {
        "name": "Test FD",
        "principal_amount": 10000.0,
        "interest_rate": 5.0,
        "start_date": (date.today() - timedelta(days=365)).isoformat(),
        "maturity_date": (date.today() + timedelta(days=365 * 4)).isoformat(),
        "compounding_frequency": "Annually",
        "interest_payout": "Cumulative",
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/fixed-deposits/",
        json=data,
        headers={"Authorization": f"Bearer {access_token}"},
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
    assert "id" in content
    assert "portfolio_id" in content
    assert "user_id" in content

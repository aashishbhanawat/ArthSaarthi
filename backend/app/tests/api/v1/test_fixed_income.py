from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.user import create_random_user


def test_create_fixed_deposit(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    portfolio_data = {"name": "Test Portfolio", "description": "Test portfolio"}
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/", headers=auth_headers, json=portfolio_data
    )
    assert response.status_code == 201
    portfolio_id = response.json()["id"]

    data = {
        "institution_name": "Test Bank",
        "principal_amount": 100000,
        "interest_rate": 7.5,
        "start_date": "2023-01-01",
        "maturity_date": "2024-01-01",
        "payout_type": "REINVESTMENT",
        "compounding_frequency": "QUARTERLY",
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio_id}/fixed-deposits",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["asset_type"] == "FIXED_DEPOSIT"
    assert content["name"] == "Test Bank FD"


def test_create_bond(client: TestClient, db: Session, get_auth_headers) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    portfolio_data = {"name": "Test Portfolio", "description": "Test portfolio"}
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/", headers=auth_headers, json=portfolio_data
    )
    assert response.status_code == 201
    portfolio_id = response.json()["id"]

    data = {
        "bond_name": "Test Bond",
        "face_value": 1000,
        "coupon_rate": 8.0,
        "purchase_price": 1010,
        "purchase_date": "2023-01-01",
        "maturity_date": "2030-01-01",
        "interest_payout_frequency": "ANNUALLY",
        "quantity": 10,
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio_id}/bonds",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["asset_type"] == "BOND"
    assert content["name"] == "Test Bond"


def test_create_ppf(client: TestClient, db: Session, get_auth_headers) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    portfolio_data = {"name": "Test Portfolio", "description": "Test portfolio"}
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/", headers=auth_headers, json=portfolio_data
    )
    assert response.status_code == 201
    portfolio_id = response.json()["id"]

    data = {
        "institution_name": "Test Post Office",
        "account_number": "123456789",
        "opening_date": "2020-01-01",
        "current_balance": 50000,
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio_id}/ppf",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["asset_type"] == "PPF"
    assert content["name"] == "PPF Account (123456789)"

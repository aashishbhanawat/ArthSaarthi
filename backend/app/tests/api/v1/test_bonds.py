from datetime import date
from decimal import Decimal
from uuid import uuid4
from typing import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.schemas.enums import BondType
from app.tests.utils.user import create_random_user
from app.tests.utils.bond import create_random_bond
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.utils import random_lower_string

# Mark all tests in this module to use the pre_unlocked_key_manager fixture
pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


@pytest.fixture(scope="function")
def normal_user_data(db: Session) -> dict:
    user, password = create_random_user(db)
    return {"email": user.email, "password": password}


def test_create_bond(
    client: TestClient, db: Session, get_auth_headers: Callable, normal_user_data: dict
) -> None:
    normal_user_token_headers = get_auth_headers(
        email=normal_user_data["email"], password=normal_user_data["password"]
    )
    user = crud.user.get_by_email(db, email=normal_user_data["email"])
    portfolio = create_test_portfolio(db, user_id=user.id, name="Bond Portfolio")
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type="BOND",
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)

    bond_data = {
        "bond_type": "CORPORATE",
        "face_value": 1000.0,
        "coupon_rate": 7.5,
        "maturity_date": "2030-01-15",
    }
    transaction_data = {
        "asset_id": str(asset.id),
        "transaction_type": "BUY",
        "quantity": 10,
        "price_per_unit": 995.0,
        "transaction_date": date.today().isoformat(),
    }
    data = {
        "bond_data": bond_data,
        "transaction_data": transaction_data,
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/bonds/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["asset_id"] == str(asset.id)
    assert content["bond_type"] == "CORPORATE"
    assert float(content["coupon_rate"]) == 7.5


def test_create_bond_for_non_bond_asset(
    client: TestClient, db: Session, get_auth_headers: Callable, normal_user_data: dict
) -> None:
    normal_user_token_headers = get_auth_headers(
        email=normal_user_data["email"], password=normal_user_data["password"]
    )
    user = crud.user.get_by_email(db, email=normal_user_data["email"])
    portfolio = create_test_portfolio(db, user_id=user.id, name="Bond Portfolio")
    asset_in = schemas.AssetCreate(
        name="Test Stock Asset",
        ticker_symbol=f"STOCK-{random_lower_string()}",
        asset_type="STOCK",
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_data = {
        "bond_type": "CORPORATE",
        "maturity_date": "2030-01-15",
    }
    transaction_data = {
        "asset_id": str(asset.id),
        "transaction_type": "BUY",
        "quantity": 10,
        "price_per_unit": 995.0,
        "transaction_date": date.today().isoformat(),
    }
    data = {
        "bond_data": bond_data,
        "transaction_data": transaction_data,
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/bonds/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert "is not a BOND type asset" in content["detail"]


def test_create_bond_for_nonexistent_asset(
    client: TestClient, db: Session, get_auth_headers: Callable, normal_user_data: dict
) -> None:
    normal_user_token_headers = get_auth_headers(
        email=normal_user_data["email"], password=normal_user_data["password"]
    )
    user = crud.user.get_by_email(db, email=normal_user_data["email"])
    portfolio = create_test_portfolio(db, user_id=user.id, name="Bond Portfolio")
    non_existent_asset_id = str(uuid4())
    bond_data = {
        "bond_type": "CORPORATE",
        "maturity_date": "2030-01-15",
    }
    transaction_data = {
        "asset_id": non_existent_asset_id,
        "transaction_type": "BUY",
        "quantity": 10,
        "price_per_unit": 995.0,
        "transaction_date": date.today().isoformat(),
    }
    data = {
        "bond_data": bond_data,
        "transaction_data": transaction_data,
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/bonds/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 404


def test_create_duplicate_bond_for_asset(
    client: TestClient, db: Session, get_auth_headers: Callable, normal_user_data: dict
) -> None:
    normal_user_token_headers = get_auth_headers(
        email=normal_user_data["email"], password=normal_user_data["password"]
    )
    user = crud.user.get_by_email(db, email=normal_user_data["email"])
    portfolio = create_test_portfolio(db, user_id=user.id, name="Bond Portfolio")
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type="BOND",
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    create_random_bond(db, asset_id=asset.id)  # First bond created
    bond_data = {
        "bond_type": "GOVERNMENT",  # New type to verify update
        "maturity_date": "2040-01-01",
        "coupon_rate": 8.0,
    }
    transaction_data = {
        "asset_id": str(asset.id),
        "transaction_type": "BUY",
        "quantity": 10,
        "price_per_unit": 995.0,
        "transaction_date": date.today().isoformat(),
    }
    data = {
        "bond_data": bond_data,
        "transaction_data": transaction_data,
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/bonds/",
        headers=normal_user_token_headers,
        json=data,
    )
    # The endpoint now supports "upsert" logic. It should succeed and update the bond.
    assert response.status_code == 201
    content = response.json()
    assert content["bond_type"] == "GOVERNMENT"
    assert float(content["coupon_rate"]) == 8.0


def test_read_bond(
    client: TestClient, db: Session, get_auth_headers: Callable, normal_user_data: dict
) -> None:
    normal_user_token_headers = get_auth_headers(
        email=normal_user_data["email"], password=normal_user_data["password"]
    )
    user = crud.user.get_by_email(db, email=normal_user_data["email"])
    portfolio = create_test_portfolio(db, user_id=user.id, name="Bond Portfolio")
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type="BOND",
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond = create_random_bond(db, asset_id=asset.id)
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/bonds/{bond.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(bond.id)
    assert content["asset_id"] == str(asset.id)
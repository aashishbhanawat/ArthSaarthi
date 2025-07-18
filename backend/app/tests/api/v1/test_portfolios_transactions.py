from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.config import settings
from app.tests.utils.user import create_random_user
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.asset import create_test_asset
from app import crud


def test_create_portfolio(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    data = {"name": "My First Portfolio"}
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["name"] == data["name"]
    assert "id" in content
    assert "user_id" in content


def test_read_portfolios(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    create_test_portfolio(db, user=user, name="Portfolio 1")
    create_test_portfolio(db, user=user, name="Portfolio 2")

    response = client.get(
        f"{settings.API_V1_STR}/portfolios/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 2


def test_read_portfolio_by_id(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user=user)

    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == portfolio.name
    assert content["id"] == portfolio.id


def test_read_portfolio_wrong_owner(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    other_user, _ = create_random_user(db) # We don't need the other user's password
    portfolio = create_test_portfolio(db, user=other_user)

    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_delete_portfolio(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user=user)

    response = client.delete(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    deleted_portfolio = crud.portfolio.get(db, id=portfolio.id)
    assert deleted_portfolio is None


def test_lookup_asset(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    response = client.get(
        f"{settings.API_V1_STR}/assets/lookup/AAPL",
        headers=auth_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "Apple Inc."
    assert content["asset_type"] == "STOCK"


def test_lookup_asset_not_found(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    response = client.get(
        f"{settings.API_V1_STR}/assets/lookup/UNKNOWNTICKER",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_create_transaction_with_new_asset(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user=user)

    data = {
        "portfolio_id": portfolio.id,
        "new_asset": {
            "ticker_symbol": "MSFT",
            "name": "Microsoft Corp",
            "asset_type": "STOCK",
            "currency": "USD"
        },
        "transaction_type": "BUY",
        "quantity": 10,
        "price_per_unit": 300.50,
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["quantity"] == "10.00000000"
    assert content["asset"]["ticker_symbol"] == "MSFT"

    # Verify asset was created in DB
    asset_in_db = crud.asset.get_by_ticker(db, ticker_symbol="MSFT")
    assert asset_in_db is not None
    assert asset_in_db.name == "Microsoft Corp"


def test_create_transaction_with_existing_asset(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user=user)
    asset = create_test_asset(db, ticker_symbol="TSLA", name="Tesla Inc.")

    data = {
        "portfolio_id": portfolio.id,
        "asset_id": asset.id,
        "transaction_type": "BUY",
        "quantity": 5,
        "price_per_unit": 250.00,
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["asset"]["id"] == asset.id


def test_create_transaction_for_other_user_portfolio(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    other_user, _ = create_random_user(db) # We don't need the other user's password
    portfolio = create_test_portfolio(db, user=other_user)
    asset = create_test_asset(db, ticker_symbol="AMZN", name="Amazon.com Inc.")

    data = {
        "portfolio_id": portfolio.id,
        "asset_id": asset.id,
        "transaction_type": "BUY",
        "quantity": 2,
        "price_per_unit": 130.00,
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 403 # Forbidden


def test_create_transaction_conflicting_asset_info(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user=user)
    asset = create_test_asset(db, ticker_symbol="NVDA", name="NVIDIA Corp")

    data = {
        "portfolio_id": portfolio.id,
        "asset_id": asset.id, # Providing both asset_id
        "new_asset": { "ticker_symbol": "NVDA", "name": "NVIDIA Corp", "asset_type": "STOCK", "currency": "USD" }, # and new_asset
        "transaction_type": "BUY",
        "quantity": 10,
        "price_per_unit": 450.00,
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 422 # Unprocessable Entity
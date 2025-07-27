from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.config import settings
from app.tests.utils.user import create_random_user
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.asset import create_test_asset
from app.tests.utils.transaction import create_test_transaction
from app import crud, schemas


def test_create_portfolio(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    data = {"name": "Test Portfolio", "description": "A test portfolio"}
    response = client.post(f"{settings.API_V1_STR}/portfolios/", headers=headers, json=data)
    assert response.status_code == 201
    content = response.json()
    assert content["name"] == data["name"]
    assert "id" in content


def test_read_portfolios(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    create_test_portfolio(db, user_id=user.id, name="Portfolio 1")
    create_test_portfolio(db, user_id=user.id, name="Portfolio 2")
    response = client.get(f"{settings.API_V1_STR}/portfolios/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_read_portfolio_by_id(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="My Portfolio")
    response = client.get(f"{settings.API_V1_STR}/portfolios/{portfolio.id}", headers=headers)
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == portfolio.name
    assert content["id"] == portfolio.id


def test_read_portfolio_wrong_owner(client: TestClient, db: Session, get_auth_headers):
    user1, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user1.id, name="User1 Portfolio")

    user2, password2 = create_random_user(db)
    headers2 = get_auth_headers(user2.email, password2)
    response = client.get(f"{settings.API_V1_STR}/portfolios/{portfolio.id}", headers=headers2)
    assert response.status_code == 403


def test_delete_portfolio(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="To Be Deleted")
    response = client.delete(f"{settings.API_V1_STR}/portfolios/{portfolio.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Portfolio deleted successfully"
    db_portfolio = crud.portfolio.get(db, id=portfolio.id)
    assert db_portfolio is None


def test_lookup_asset(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    create_test_asset(db, ticker_symbol="AAPL", name="Apple Inc.")
    response = client.get(f"{settings.API_V1_STR}/assets/lookup/?query=AAPL", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker_symbol"] == "AAPL"


def test_create_transaction_with_existing_asset(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="My Portfolio")
    asset = create_test_asset(db, ticker_symbol="GOOGL", name="Alphabet Inc.")
    data = {
        "asset_id": asset.id,
        "transaction_type": "BUY",
        "quantity": 10,
        "price_per_unit": 150.00,
        "transaction_date": datetime.now(timezone.utc).isoformat(),
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/transactions/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["asset"]["ticker_symbol"] == "GOOGL"
    assert float(content["quantity"]) == 10.0


def test_create_transaction_for_other_user_portfolio(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user1, _ = create_random_user(db)
    portfolio1 = create_test_portfolio(db, user_id=user1.id, name="User1 Portfolio")

    user2, password2 = create_random_user(db)
    auth_headers2 = get_auth_headers(user2.email, password2)

    asset = create_test_asset(db, ticker_symbol="TSLA", name="Tesla Inc.")
    data = {
        "asset_id": asset.id,
        "transaction_type": "BUY",
        "quantity": 5,
        "price_per_unit": 250.00,
        "transaction_date": datetime.now(timezone.utc).isoformat(),
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio1.id}/transactions/",
        headers=auth_headers2,
        json=data,
    )
    assert response.status_code == 403


def test_read_assets(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    create_test_asset(db, ticker_symbol="MSFT")
    create_test_asset(db, ticker_symbol="AMZN")
    response = client.get(f"{settings.API_V1_STR}/assets/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_read_asset_by_id(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    asset = create_test_asset(db, ticker_symbol="NFLX")
    response = client.get(f"{settings.API_V1_STR}/assets/{asset.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["ticker_symbol"] == "NFLX"


def test_read_asset_by_id_not_found(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    response = client.get(f"{settings.API_V1_STR}/assets/99999", headers=headers)
    assert response.status_code == 404
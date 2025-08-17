import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.tests.utils.user import create_random_user


def test_create_portfolio(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    data = {"name": "Test Portfolio", "description": "A test portfolio"}
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/", headers=headers, json=data
    )
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
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}", headers=headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == portfolio.name
    assert content["id"] == str(portfolio.id)


def test_read_portfolio_wrong_owner(client: TestClient, db: Session, get_auth_headers):
    user1, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user1.id, name="User1 Portfolio")

    user2, password2 = create_random_user(db)
    headers2 = get_auth_headers(user2.email, password2)
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}", headers=headers2
    )
    assert response.status_code == 403


def test_delete_portfolio(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="To Be Deleted")
    response = client.delete(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "Portfolio deleted successfully"
    db_portfolio = crud.portfolio.get(db, id=portfolio.id)
    assert db_portfolio is None


def test_lookup_asset(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    create_test_asset(db, ticker_symbol="AAPL", name="Apple Inc.")
    response = client.get(
        f"{settings.API_V1_STR}/assets/lookup/?query=AAPL", headers=headers
    )
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
        "asset_id": str(asset.id),
        "transaction_type": "BUY",
        "quantity": 10,
        "price_per_unit": 150.00,
        "transaction_date": datetime.now(timezone.utc).isoformat(),
        "fees": 0.0,
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
        "asset_id": str(asset.id),
        "transaction_type": "BUY",
        "quantity": 5,
        "price_per_unit": 250.00,
        "transaction_date": datetime.now(timezone.utc).isoformat(),
        "fees": 0.0,
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
    non_existent_uuid = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/assets/{non_existent_uuid}", headers=headers
    )
    assert response.status_code == 404


def test_update_transaction(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Update Portfolio")
    transaction = create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="UPDATE",
        quantity=10,
        price_per_unit=100.0,
    )

    update_data = {"quantity": 15.5}
    response = client.put(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/transactions/{transaction.id}",
        headers=headers,
        json=update_data,
    )

    assert response.status_code == 200
    content = response.json()
    assert float(content["quantity"]) == 15.5
    assert content["id"] == str(transaction.id)


def test_update_transaction_not_found(
    client: TestClient, db: Session, get_auth_headers
):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Dummy Portfolio")
    non_existent_uuid = uuid.uuid4()
    update_data = {"quantity": 15}

    response = client.put(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/transactions/{non_existent_uuid}",
        headers=headers,
        json=update_data,
    )
    assert response.status_code == 404


def test_update_transaction_wrong_owner(
    client: TestClient, db: Session, get_auth_headers
):
    user1, _ = create_random_user(db)
    portfolio1 = create_test_portfolio(db, user_id=user1.id, name="User1 Portfolio")
    transaction1 = create_test_transaction(
        db, portfolio_id=portfolio1.id, ticker="OWNED", quantity=10
    )

    user2, password2 = create_random_user(db)
    headers2 = get_auth_headers(user2.email, password2)
    update_data = {"quantity": 20}

    response = client.put(
        f"{settings.API_V1_STR}/portfolios/{portfolio1.id}/transactions/{transaction1.id}",
        headers=headers2,
        json=update_data,
    )
    assert response.status_code == 403


def test_delete_transaction(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Delete Portfolio")
    transaction = create_test_transaction(
        db, portfolio_id=portfolio.id, ticker="DELETE", quantity=5
    )
    transaction_id = transaction.id

    response = client.delete(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/transactions/{transaction_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["msg"] == "Transaction deleted successfully"
    db_transaction = crud.transaction.get(db, id=transaction_id)
    assert db_transaction is None

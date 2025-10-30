from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.services.financial_data_service import financial_data_service
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_create_transaction_with_existing_asset(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """
    Test creating a transaction for a stock that already exists in the database.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="My Portfolio")
    asset = create_test_asset(db, ticker_symbol="RELIANCE", name="Reliance Industries")

    transaction_payload = {
        "ticker_symbol": "RELIANCE",
        "asset_type": "Stock",
        "transaction_type": "BUY",
        "quantity": 10.0,
        "price_per_unit": 2500.00,
        "transaction_date": datetime.now(timezone.utc).isoformat(),
        "fees": 0.0,
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/?portfolio_id={portfolio.id}",
        headers=auth_headers,
        json=transaction_payload,
    )
    assert response.status_code == 201, response.json()
    content_list = response.json()
    assert isinstance(content_list, list)
    assert len(content_list) == 1
    content = content_list[0]
    assert Decimal(content["quantity"]) == Decimal("10.0")
    assert content["asset"]["id"] == str(asset.id)
    assert content["asset"]["ticker_symbol"] == "RELIANCE"
    assert content["portfolio_id"] == str(portfolio.id)


def test_create_transaction_with_new_mutual_fund_asset(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    """
    Test creating a transaction for a Mutual Fund that does not exist locally.
    This should trigger the get_or_create_by_ticker logic to create the asset.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="MF Portfolio")

    mf_scheme_code = "123456"
    mock_mf_details = {
        "name": "Test Mutual Fund - Growth",
        "asset_type": "Mutual Fund",
        "exchange": "AMFI",
        "currency": "INR",
        "isin": "INF123456789",
    }

    mocker.patch.object(
        financial_data_service, "get_asset_details", return_value=mock_mf_details
    )

    transaction_payload = {
        "ticker_symbol": mf_scheme_code,
        "asset_type": "Mutual Fund",
        "transaction_type": "BUY",
        "quantity": 100.5,
        "price_per_unit": 10.50,
        "transaction_date": "2025-08-22T10:00:00",
        "fees": 5.0,
    }

    response = client.post(
        f"{settings.API_V1_STR}/transactions/?portfolio_id={portfolio.id}",
        headers=auth_headers,
        json=transaction_payload,
    )
    assert response.status_code == 201, response.json()
    data_list = response.json()
    assert isinstance(data_list, list)
    assert len(data_list) == 1
    data = data_list[0]
    assert Decimal(data["quantity"]) == Decimal("100.5")
    assert data["asset"]["ticker_symbol"] == mf_scheme_code
    assert data["asset"]["name"] == "Test Mutual Fund - Growth"
    assert data["asset"]["exchange"] == "AMFI"

    financial_data_service.get_asset_details.assert_called_once_with(
        mf_scheme_code, asset_type="Mutual Fund"
    )

    db_asset = crud.asset.get_by_ticker(db, ticker_symbol=mf_scheme_code)
    assert db_asset is not None
    assert db_asset.name == "Test Mutual Fund - Growth"
    assert db_asset.isin == "INF123456789"


def test_create_transaction_for_other_user_portfolio(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user1, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user1.id, name="User1 Portfolio")

    user2, password2 = create_random_user(db)
    auth_headers2 = get_auth_headers(user2.email, password2)

    transaction_payload = {
        "ticker_symbol": "TCS",
        "asset_type": "Stock",
        "transaction_type": "BUY",
        "quantity": 5,
        "price_per_unit": 250.00,
        "transaction_date": datetime.now(timezone.utc).isoformat(),
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/?portfolio_id={portfolio.id}",
        headers=auth_headers2,
        json=transaction_payload,
    )
    assert response.status_code == 403


def test_read_transactions_with_filters_and_pagination(
    client: TestClient, db: Session, get_auth_headers
):
    """
    Test reading transactions with various filters and pagination.
    """
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Filter Test Portfolio")

    asset1 = create_test_asset(db, ticker_symbol="ASSET1")
    asset2 = create_test_asset(db, ticker_symbol="ASSET2")

    tx1_date = datetime.now(timezone.utc) - timedelta(days=20)
    tx2_date = datetime.now(timezone.utc) - timedelta(days=10)
    tx3_date = datetime.now(timezone.utc) - timedelta(days=5)

    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker=asset1.ticker_symbol,
        transaction_date=tx1_date,
        quantity=10,
        price_per_unit=100,
    )
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker=asset2.ticker_symbol,
        transaction_date=tx2_date,
        quantity=20,
        price_per_unit=200,
    )
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker=asset1.ticker_symbol,
        transaction_type="SELL",
        transaction_date=tx3_date,
        quantity=5,
        price_per_unit=110,
    )

    base_url = f"{settings.API_V1_STR}/transactions/"

    # 1. Test filter by portfolio_id
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["transactions"]) == 3

    # 2. Test filter by asset_id
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}&asset_id={asset1.id}", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(tx["asset"]["id"] == str(asset1.id) for tx in data["transactions"])

    # 3. Test filter by transaction_type
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}&transaction_type=BUY", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(tx["transaction_type"] == "BUY" for tx in data["transactions"])

    # 4. Test filter by date range (last 15 days)
    start_date_str = (
        datetime.now(timezone.utc) - timedelta(days=15)
    ).date().isoformat()
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}&start_date={start_date_str}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # tx2 and tx3

    # 5. Test pagination
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}&skip=1&limit=1", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["transactions"]) == 1


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
        f"{settings.API_V1_STR}/transactions/{transaction.id}?portfolio_id={portfolio.id}",
        headers=headers,
        json=update_data,
    )

    assert response.status_code == 200
    content = response.json()
    assert float(content["quantity"]) == 15.5
    assert content["id"] == str(transaction.id)


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
        f"{settings.API_V1_STR}/transactions/{transaction1.id}?portfolio_id={portfolio1.id}",
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
        f"{settings.API_V1_STR}/transactions/{transaction_id}?portfolio_id={portfolio.id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["msg"] == "Transaction deleted successfully"
    db_transaction = crud.transaction.get(db, id=transaction_id)
    assert db_transaction is None

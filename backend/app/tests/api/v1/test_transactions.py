import uuid
from datetime import datetime, timedelta
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.schemas.transaction import TransactionCreate
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_read_transactions_unauthorized(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    """
    Test that a user cannot read transactions from a portfolio they do not own.
    """
    user1, _ = create_random_user(db)
    user2, user2_password = create_random_user(db)
    user2_headers = get_auth_headers(user2.email, user2_password)

    portfolio1 = create_test_portfolio(db, user_id=user1.id, name="User 1 Portfolio")

    response = client.get(
        f"{settings.API_V1_STR}/transactions/?portfolio_id={portfolio1.id}",
        headers=user2_headers,
    )
    assert response.status_code == 403, response.json()
    assert "Not enough permissions" in response.json()["detail"]


def test_read_transactions_not_found(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    """
    Test that reading transactions from a non-existent portfolio returns 404.
    """
    user, password = create_random_user(db)
    non_existent_uuid = uuid.uuid4()
    user_headers = get_auth_headers(user.email, password)

    response = client.get(
        f"{settings.API_V1_STR}/transactions/?portfolio_id={non_existent_uuid}",
        headers=user_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Portfolio not found"


def test_read_transactions_with_filters_and_pagination(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    """
    Test reading transactions with various filters and pagination.
    """
    user, password = create_random_user(db)
    user_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Filter Test Portfolio")

    asset1 = create_test_asset(db, ticker_symbol="ASSET1")
    asset2 = create_test_asset(db, ticker_symbol="ASSET2")

    # Create some transactions with different dates, types, and assets
    tx1_date = datetime.utcnow() - timedelta(days=20)
    tx2_date = datetime.utcnow() - timedelta(days=10)
    tx3_date = datetime.utcnow() - timedelta(days=5)

    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=asset1.id,
            transaction_type="BUY",
            quantity=10,
            price_per_unit=100,
            transaction_date=tx1_date,
            fees=0,
        ),
        portfolio_id=portfolio.id,
    )
    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=asset2.id,
            transaction_type="BUY",
            quantity=5,
            price_per_unit=200,
            transaction_date=tx2_date,
            fees=0,
        ),
        portfolio_id=portfolio.id,
    )
    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=asset1.id,
            transaction_type="SELL",
            quantity=5,
            price_per_unit=110,
            transaction_date=tx3_date,
            fees=0,
        ),
        portfolio_id=portfolio.id,
    )
    db.commit()

    base_url = f"{settings.API_V1_STR}/transactions/"

    # 1. Test no filters (should get all 3, sorted by date desc)
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}", headers=user_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["transactions"]) == 3

    # 2. Test filter by asset_id
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}&asset_id={asset1.id}",
        headers=user_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(tx["asset"]["id"] == str(asset1.id) for tx in data["transactions"])

    # 3. Test filter by transaction_type
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}&transaction_type=BUY",
        headers=user_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(tx["transaction_type"] == "BUY" for tx in data["transactions"])

    # 4. Test filter by date range (last 15 days)
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}&start_date={tx2_date.date().isoformat()}",
        headers=user_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # tx2 and tx3

    # 5. Test combination of filters (ASSET1 and SELL)
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}&asset_id={asset1.id}&transaction_type=SELL",
        headers=user_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["transactions"][0]["asset"]["ticker_symbol"] == "ASSET1"
    assert data["transactions"][0]["transaction_type"] == "SELL"

    # 6. Test pagination
    response = client.get(
        f"{base_url}?portfolio_id={portfolio.id}&skip=1&limit=1", headers=user_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["transactions"]) == 1


def test_get_available_lots_multi_portfolio(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    """
    Test that available lots can be filtered by portfolio_id and that
    permissions are enforced.
    """
    from decimal import Decimal

    # Create main user and their headers
    user, password = create_random_user(db)
    user_headers = get_auth_headers(user.email, password)

    # Create two portfolios for the same user
    portfolio1 = create_test_portfolio(db, user_id=user.id, name="Portfolio 1")
    portfolio2 = create_test_portfolio(db, user_id=user.id, name="Portfolio 2")

    # Create a test asset
    asset = create_test_asset(db, ticker_symbol="TEST_LOTS_ASSET")

    # Create buy transaction in Portfolio 1
    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=asset.id,
            transaction_type="BUY",
            quantity=10,
            price_per_unit=100,
            transaction_date=datetime.utcnow() - timedelta(days=2),
            fees=0,
        ),
        portfolio_id=portfolio1.id,
    )

    # Create buy transaction in Portfolio 2
    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=asset.id,
            transaction_type="BUY",
            quantity=15,
            price_per_unit=200,
            transaction_date=datetime.utcnow() - timedelta(days=1),
            fees=0,
        ),
        portfolio_id=portfolio2.id,
    )
    db.commit()

    base_url = f"{settings.API_V1_STR}/transactions/available-lots/{asset.id}"

    # 1. Fetch available lots without portfolio filter (should return both lots)
    response = client.get(base_url, headers=user_headers)
    assert response.status_code == 200, response.json()
    lots = response.json()
    assert len(lots) == 2
    total_qty = sum(Decimal(lot["available_quantity"]) for lot in lots)
    assert total_qty == Decimal("25")

    # 2. Fetch available lots filtered by Portfolio 1
    response = client.get(
        f"{base_url}?portfolio_id={portfolio1.id}", headers=user_headers
    )
    assert response.status_code == 200, response.json()
    lots1 = response.json()
    assert len(lots1) == 1
    assert Decimal(lots1[0]["available_quantity"]) == Decimal("10")

    # 3. Fetch available lots filtered by Portfolio 2
    response = client.get(
        f"{base_url}?portfolio_id={portfolio2.id}", headers=user_headers
    )
    assert response.status_code == 200, response.json()
    lots2 = response.json()
    assert len(lots2) == 1
    assert Decimal(lots2[0]["available_quantity"]) == Decimal("15")

    # 4. Verify IDOR security checks (unauthorized access to portfolio)
    other_user, other_password = create_random_user(db)
    other_headers = get_auth_headers(other_user.email, other_password)

    response = client.get(
        f"{base_url}?portfolio_id={portfolio1.id}", headers=other_headers
    )
    assert response.status_code == 403, response.json()
    assert "Not enough permissions" in response.json()["detail"]

    # 5. Verify non-existent portfolio ID returns 404
    non_existent_uuid = uuid.uuid4()
    response = client.get(
        f"{base_url}?portfolio_id={non_existent_uuid}", headers=user_headers
    )
    assert response.status_code == 404, response.json()
    assert "Portfolio not found" in response.json()["detail"]

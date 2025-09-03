import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.utils.asset import create_test_asset
from app.tests.utils.user import create_random_user
from app.tests.utils.watchlist import create_random_watchlist

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_create_watchlist(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    watchlist_name = "My Test Watchlist"
    response = client.post(
        "/api/v1/watchlists/",
        headers=headers,
        json={"name": watchlist_name},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == watchlist_name
    assert data["user_id"] == str(user.id)


def test_read_watchlists(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    create_random_watchlist(db, user_id=user.id)
    create_random_watchlist(db, user_id=user.id)

    response = client.get("/api/v1/watchlists/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_read_watchlist_by_id(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    watchlist = create_random_watchlist(db, user_id=user.id)

    response = client.get(f"/api/v1/watchlists/{watchlist.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == watchlist.name
    assert data["id"] == str(watchlist.id)


def test_read_watchlist_not_found(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    import uuid

    non_existent_id = uuid.uuid4()
    response = client.get(f"/api/v1/watchlists/{non_existent_id}", headers=headers)
    assert response.status_code == 404


def test_read_watchlist_not_owned(client: TestClient, db: Session, get_auth_headers):
    user1, password = create_random_user(db)
    user2, _ = create_random_user(db)
    headers = get_auth_headers(user1.email, password)
    watchlist_for_user2 = create_random_watchlist(db, user_id=user2.id)

    url = f"/api/v1/watchlists/{watchlist_for_user2.id}"
    response = client.get(url, headers=headers)
    assert response.status_code == 403


def test_update_watchlist(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    watchlist = create_random_watchlist(db, user_id=user.id)
    new_name = "Updated Watchlist Name"

    response = client.put(
        f"/api/v1/watchlists/{watchlist.id}",
        headers=headers,
        json={"name": new_name},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_name
    assert data["id"] == str(watchlist.id)


def test_delete_watchlist(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    watchlist = create_random_watchlist(db, user_id=user.id)

    response = client.delete(f"/api/v1/watchlists/{watchlist.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(watchlist.id)

    # Verify it's gone
    response = client.get(f"/api/v1/watchlists/{watchlist.id}", headers=headers)
    assert response.status_code == 404


def test_add_item_to_watchlist(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    watchlist = create_random_watchlist(db, user_id=user.id)
    asset = create_test_asset(db, ticker_symbol="AAPL")

    response = client.post(
        f"/api/v1/watchlists/{watchlist.id}/items",
        headers=headers,
        json={"asset_id": str(asset.id)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["asset_id"] == str(asset.id)
    assert data["watchlist_id"] == str(watchlist.id)


def test_add_duplicate_item_to_watchlist_fails(
    client: TestClient, db: Session, get_auth_headers
):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    watchlist = create_random_watchlist(db, user_id=user.id)
    asset = create_test_asset(db, ticker_symbol="GOOG")
    # Add it once
    client.post(
        f"/api/v1/watchlists/{watchlist.id}/items",
        headers=headers,
        json={"asset_id": str(asset.id)},
    )
    # Try to add it again
    response = client.post(
        f"/api/v1/watchlists/{watchlist.id}/items",
        headers=headers,
        json={"asset_id": str(asset.id)},
    )
    assert response.status_code == 400


def test_remove_item_from_watchlist(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    watchlist = create_random_watchlist(db, user_id=user.id)
    asset = create_test_asset(db, ticker_symbol="MSFT")
    # Add the item
    response = client.post(
        f"/api/v1/watchlists/{watchlist.id}/items",
        headers=headers,
        json={"asset_id": str(asset.id)},
    )
    item_id = response.json()["id"]

    # Remove it
    response = client.delete(
        f"/api/v1/watchlists/{watchlist.id}/items/{item_id}", headers=headers
    )
    assert response.status_code == 200

    # Verify it's gone
    response = client.get(f"/api/v1/watchlists/{watchlist.id}", headers=headers)
    data = response.json()
    assert len(data["items"]) == 0


def test_read_watchlist_with_items(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    # Mock the financial data service
    mock_price_data = {
        "TSLA": {"current_price": 180.0, "previous_close": 177.5},
        "NVDA": {"current_price": 450.0, "previous_close": 455.0},
    }
    mocker.patch(
        "app.services.financial_data_service.financial_data_service.get_current_prices",
        return_value=mock_price_data,
    )

    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    watchlist = create_random_watchlist(db, user_id=user.id)
    asset1 = create_test_asset(db, ticker_symbol="TSLA")
    asset2 = create_test_asset(db, ticker_symbol="NVDA")
    client.post(
        f"/api/v1/watchlists/{watchlist.id}/items",
        headers=headers,
        json={"asset_id": str(asset1.id)},
    )
    client.post(
        f"/api/v1/watchlists/{watchlist.id}/items",
        headers=headers,
        json={"asset_id": str(asset2.id)},
    )

    response = client.get(f"/api/v1/watchlists/{watchlist.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2

    # Create a map of ticker to item for easier assertion
    items_by_ticker = {item["asset"]["ticker_symbol"]: item for item in data["items"]}
    assert "TSLA" in items_by_ticker
    assert "NVDA" in items_by_ticker

    # Check that the price data was added
    assert items_by_ticker["TSLA"]["asset"]["current_price"] == 180.0
    assert items_by_ticker["TSLA"]["asset"]["day_change"] == 2.5
    assert items_by_ticker["NVDA"]["asset"]["current_price"] == 450.0
    assert items_by_ticker["NVDA"]["asset"]["day_change"] == -5.0

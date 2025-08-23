from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.asset import create_random_asset
from app.tests.utils.user import create_random_user
from app.tests.utils.watchlist import create_random_watchlist


def test_add_watchlist_item(client: TestClient, db: Session) -> None:
    user, _ = create_random_user(db, client)
    user_headers = {"Authorization": f"Bearer {user.token}"}
    watchlist = create_random_watchlist(db, user_id=user.id)
    asset = create_random_asset(db)
    data = {"asset_id": str(asset.id)}
    response = client.post(
        f"{settings.API_V1_STR}/watchlists/{watchlist.id}/items",
        headers=user_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["asset_id"] == data["asset_id"]
    assert "id" in content
    assert "watchlist_id" in content


def test_remove_watchlist_item(client: TestClient, db: Session) -> None:
    user, _ = create_random_user(db, client)
    user_headers = {"Authorization": f"Bearer {user.token}"}
    watchlist = create_random_watchlist(db, user_id=user.id)
    asset = create_random_asset(db)
    item_data = {"asset_id": str(asset.id)}
    item_response = client.post(
        f"{settings.API_V1_STR}/watchlists/{watchlist.id}/items",
        headers=user_headers,
        json=item_data,
    )
    item_id = item_response.json()["id"]
    response = client.delete(
        f"{settings.API_V1_STR}/watchlists/{watchlist.id}/items/{item_id}",
        headers=user_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["msg"] == "Item removed successfully"

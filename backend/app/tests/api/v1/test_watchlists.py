from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.user import create_random_user


def test_create_watchlist(client: TestClient, db: Session) -> None:
    user, _ = create_random_user(db, client)
    user_headers = {"Authorization": f"Bearer {user.token}"}
    data = {"name": "My Watchlist"}
    response = client.post(
        f"{settings.API_V1_STR}/watchlists/",
        headers=user_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["name"] == data["name"]
    assert "id" in content
    assert "user_id" in content


def test_read_watchlists(client: TestClient, db: Session) -> None:
    user, _ = create_random_user(db, client)
    user_headers = {"Authorization": f"Bearer {user.token}"}
    data = {"name": "My Watchlist"}
    client.post(
        f"{settings.API_V1_STR}/watchlists/",
        headers=user_headers,
        json=data,
    )
    response = client.get(
        f"{settings.API_V1_STR}/watchlists/",
        headers=user_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 1
    assert content[0]["name"] == data["name"]

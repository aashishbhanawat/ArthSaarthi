from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.user import create_random_user
from app.tests.utils.watchlist import create_random_watchlist


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

    response = client.get(f"/api/v1/watchlists/{watchlist_for_user2.id}", headers=headers)
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

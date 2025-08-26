import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.utils.asset import create_test_asset
from app.tests.utils.goal import create_random_goal
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_create_goal(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal_data = {
        "name": "Buy a car",
        "target_amount": 25000.00,
        "target_date": "2025-12-31",
    }
    response = client.post(
        "/api/v1/goals/",
        headers=headers,
        json=goal_data,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == goal_data["name"]
    assert data["target_amount"] == goal_data["target_amount"]
    assert data["target_date"] == goal_data["target_date"]
    assert data["user_id"] == str(user.id)


def test_read_goals(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    create_random_goal(db, user_id=user.id)
    create_random_goal(db, user_id=user.id)

    response = client.get("/api/v1/goals/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_read_goal_by_id(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)

    response = client.get(f"/api/v1/goals/{goal.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == goal.name
    assert data["id"] == str(goal.id)


def test_read_goal_not_found(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    non_existent_id = uuid.uuid4()
    response = client.get(f"/api/v1/goals/{non_existent_id}", headers=headers)
    assert response.status_code == 404


def test_read_goal_not_owned(client: TestClient, db: Session, get_auth_headers):
    user1, password = create_random_user(db)
    user2, _ = create_random_user(db)
    headers = get_auth_headers(user1.email, password)
    goal_for_user2 = create_random_goal(db, user_id=user2.id)

    url = f"/api/v1/goals/{goal_for_user2.id}"
    response = client.get(url, headers=headers)
    assert response.status_code == 403


def test_update_goal(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)
    new_name = "Updated Goal Name"
    new_target_amount = 30000.00
    new_target_date = "2026-12-31"

    response = client.put(
        f"/api/v1/goals/{goal.id}",
        headers=headers,
        json={
            "name": new_name,
            "target_amount": new_target_amount,
            "target_date": new_target_date,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_name
    assert data["target_amount"] == new_target_amount
    assert data["target_date"] == new_target_date
    assert data["id"] == str(goal.id)


def test_delete_goal(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)

    response = client.delete(f"/api/v1/goals/{goal.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["msg"] == "Goal deleted successfully"

    # Verify it's gone
    response = client.get(f"/api/v1/goals/{goal.id}", headers=headers)
    assert response.status_code == 404


def test_create_goal_link_with_asset(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)
    asset = create_test_asset(db, ticker_symbol="AAPL")
    link_data = {"goal_id": str(goal.id), "asset_id": str(asset.id)}

    response = client.post(
        f"/api/v1/goals/{goal.id}/links", headers=headers, json=link_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["goal_id"] == str(goal.id)
    assert data["asset_id"] == str(asset.id)
    assert data["portfolio_id"] is None


def test_create_goal_link_with_portfolio(
    client: TestClient, db: Session, get_auth_headers
):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    link_data = {"goal_id": str(goal.id), "portfolio_id": str(portfolio.id)}

    response = client.post(
        f"/api/v1/goals/{goal.id}/links", headers=headers, json=link_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["goal_id"] == str(goal.id)
    assert data["portfolio_id"] == str(portfolio.id)
    assert data["asset_id"] is None


def test_delete_goal_link(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)
    asset = create_test_asset(db, ticker_symbol="GOOG")
    link_data = {"goal_id": str(goal.id), "asset_id": str(asset.id)}
    response = client.post(
        f"/api/v1/goals/{goal.id}/links", headers=headers, json=link_data
    )
    link_id = response.json()["id"]

    response = client.delete(
        f"/api/v1/goals/{goal.id}/links/{link_id}", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["msg"] == "Link deleted successfully"

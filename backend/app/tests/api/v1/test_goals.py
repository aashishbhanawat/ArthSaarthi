from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_create_goal(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    data = {
        "name": "Buy a car",
        "target_amount": 25000.00,
        "target_date": (date.today() + timedelta(days=365)).isoformat(),
    }
    response = client.post(
        f"{settings.API_V1_STR}/goals/", headers=headers, json=data
    )
    assert response.status_code == 201
    content = response.json()
    assert content["name"] == data["name"]
    assert "id" in content


def test_read_goals(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    # Create some goals for the user
    goal1_data = {
        "name": "Goal 1",
        "target_amount": 1000,
        "target_date": date.today().isoformat(),
    }
    client.post(f"{settings.API_V1_STR}/goals/", headers=headers, json=goal1_data)
    goal2_data = {
        "name": "Goal 2",
        "target_amount": 2000,
        "target_date": date.today().isoformat(),
    }
    client.post(f"{settings.API_V1_STR}/goals/", headers=headers, json=goal2_data)

    response = client.get(f"{settings.API_V1_STR}/goals/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_read_goal_by_id(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    goal_data = {
        "name": "My Goal",
        "target_amount": 5000,
        "target_date": date.today().isoformat(),
    }
    create_response = client.post(
        f"{settings.API_V1_STR}/goals/", headers=headers, json=goal_data
    )
    goal_id = create_response.json()["id"]

    response = client.get(f"{settings.API_V1_STR}/goals/{goal_id}", headers=headers)
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "My Goal"
    assert content["id"] == goal_id


def test_update_goal(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    goal_data = {
        "name": "Old Name",
        "target_amount": 1000,
        "target_date": date.today().isoformat(),
    }
    create_response = client.post(
        f"{settings.API_V1_STR}/goals/", headers=headers, json=goal_data
    )
    goal_id = create_response.json()["id"]

    update_data = {"name": "New Name"}
    response = client.put(
        f"{settings.API_V1_STR}/goals/{goal_id}",
        headers=headers,
        json=update_data,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "New Name"


def test_delete_goal(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    goal_data = {
        "name": "To Be Deleted",
        "target_amount": 100,
        "target_date": date.today().isoformat(),
    }
    create_response = client.post(
        f"{settings.API_V1_STR}/goals/", headers=headers, json=goal_data
    )
    goal_id = create_response.json()["id"]

    response = client.delete(f"{settings.API_V1_STR}/goals/{goal_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["msg"] == "Goal deleted successfully"


def test_create_goal_link_portfolio(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    goal_data = {
        "name": "Link Goal",
        "target_amount": 10000,
        "target_date": date.today().isoformat(),
    }
    goal_res = client.post(
        f"{settings.API_V1_STR}/goals/", headers=headers, json=goal_data
    )
    goal_id = goal_res.json()["id"]

    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")

    link_data = {"portfolio_id": str(portfolio.id)}
    response = client.post(
        f"{settings.API_V1_STR}/goals/{goal_id}/links",
        headers=headers,
        json=link_data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["portfolio_id"] == str(portfolio.id)
    assert content["goal_id"] == goal_id


def test_create_goal_link_asset(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    goal_data = {
        "name": "Link Goal",
        "target_amount": 10000,
        "target_date": date.today().isoformat(),
    }
    goal_res = client.post(
        f"{settings.API_V1_STR}/goals/", headers=headers, json=goal_data
    )
    goal_id = goal_res.json()["id"]

    asset = create_test_asset(db, ticker_symbol="TSLA")

    link_data = {"asset_id": str(asset.id)}
    response = client.post(
        f"{settings.API_V1_STR}/goals/{goal_id}/links",
        headers=headers,
        json=link_data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["asset_id"] == str(asset.id)
    assert content["goal_id"] == goal_id


def test_delete_goal_link(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    goal_data = {
        "name": "Link Goal",
        "target_amount": 10000,
        "target_date": date.today().isoformat(),
    }
    goal_res = client.post(
        f"{settings.API_V1_STR}/goals/", headers=headers, json=goal_data
    )
    goal_id = goal_res.json()["id"]

    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")

    link_data = {"portfolio_id": str(portfolio.id)}
    link_res = client.post(
        f"{settings.API_V1_STR}/goals/{goal_id}/links",
        headers=headers,
        json=link_data,
    )
    link_id = link_res.json()["id"]

    response = client.delete(
        f"{settings.API_V1_STR}/goals/{goal_id}/links/{link_id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "Link deleted successfully"

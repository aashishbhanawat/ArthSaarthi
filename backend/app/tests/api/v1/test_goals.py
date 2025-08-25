from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.tests.utils.goal import create_random_goal
from app.tests.utils.user import create_random_user


def test_create_goal_success(client: TestClient, db: Session, get_auth_headers):
    """
    Test successful creation of a new goal.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    goal_in = {
        "name": "Buy a car",
        "target_amount": 25000.00,
        "target_date": "2025-12-31",
    }

    response = client.post(
        f"{settings.API_V1_STR}/goals/",
        headers=auth_headers,
        json=goal_in,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == goal_in["name"]
    assert float(data["target_amount"]) == goal_in["target_amount"]
    assert data["target_date"] == goal_in["target_date"]
    assert "id" in data

    db_goal = crud.goal.get(db, id=data["id"])
    assert db_goal is not None
    assert db_goal.name == goal_in["name"]
    assert db_goal.user_id == user.id


def test_read_goals_success(client: TestClient, db: Session, get_auth_headers):
    """
    Test successful retrieval of all goals for a user.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    create_random_goal(db, user_id=user.id)
    create_random_goal(db, user_id=user.id)

    response = client.get(f"{settings.API_V1_STR}/goals/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_read_goal_success(client: TestClient, db: Session, get_auth_headers):
    """
    Test successful retrieval of a single goal.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    goal = create_random_goal(db, user_id=user.id)

    response = client.get(
        f"{settings.API_V1_STR}/goals/{goal.id}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == goal.name
    assert data["id"] == str(goal.id)


def test_update_goal_success(client: TestClient, db: Session, get_auth_headers):
    """
    Test successful update of a goal.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    goal = create_random_goal(db, user_id=user.id)

    update_data = {"name": "New Goal Name"}

    response = client.put(
        f"{settings.API_V1_STR}/goals/{goal.id}",
        headers=auth_headers,
        json=update_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["id"] == str(goal.id)

    db_goal = crud.goal.get(db, id=goal.id)
    assert db_goal.name == update_data["name"]


def test_delete_goal_success(client: TestClient, db: Session, get_auth_headers):
    """
    Test successful deletion of a goal.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    goal = create_random_goal(db, user_id=user.id)

    response = client.delete(
        f"{settings.API_V1_STR}/goals/{goal.id}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["msg"] == "Goal deleted successfully"

    db_goal = crud.goal.get(db, id=goal.id)
    assert db_goal is None

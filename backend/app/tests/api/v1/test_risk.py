import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_read_risk_profile_not_found(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    response = client.get("/api/v1/risk/", headers=headers)
    assert response.status_code == 404


def test_create_risk_profile(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    # Valid answers representing Moderate risk:
    # Q1: B (4), Q2: B (4), Q3: C (3)
    # Q4: C (3), Q5: C (3), Q6: B (2) -> Score: 19 (Moderate)
    answers = {
        "q1": "B",
        "q2": "B",
        "q3": "C",
        "q4": "C",
        "q5": "C",
        "q6": "B"
    }

    response = client.post(
        "/api/v1/risk/",
        headers=headers,
        json={"answers": answers},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["answers"] == answers
    assert data["score"] == 19
    assert data["risk_category"] == "Moderate"
    assert data["user_id"] == str(user.id)


def test_create_risk_profile_invalid(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    # Missing q6
    answers_missing = {
        "q1": "A",
        "q2": "A",
        "q3": "A",
        "q4": "A",
        "q5": "A"
    }
    response = client.post(
        "/api/v1/risk/",
        headers=headers,
        json={"answers": answers_missing},
    )
    assert response.status_code == 422

    # Invalid choice "E"
    answers_invalid_choice = {
        "q1": "A",
        "q2": "A",
        "q3": "A",
        "q4": "A",
        "q5": "A",
        "q6": "E"
    }
    response = client.post(
        "/api/v1/risk/",
        headers=headers,
        json={"answers": answers_invalid_choice},
    )
    assert response.status_code == 422


def test_update_risk_profile(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    # Initial profile: Conservative
    answers_1 = {
        "q1": "D", # 1
        "q2": "D", # 1
        "q3": "A", # 1
        "q4": "A", # 1
        "q5": "A", # 1
        "q6": "A"  # 1  -> Score: 6 (Conservative)
    }
    response = client.post(
        "/api/v1/risk/",
        headers=headers,
        json={"answers": answers_1},
    )
    assert response.status_code == 201
    assert response.json()["risk_category"] == "Conservative"

    # Update profile: Aggressive
    answers_2 = {
        "q1": "A", # 6
        "q2": "A", # 6
        "q3": "D", # 4
        "q4": "D", # 4
        "q5": "D", # 4
        "q6": "D"  # 4  -> Score: 28 (Aggressive)
    }
    response = client.post(
        "/api/v1/risk/",
        headers=headers,
        json={"answers": answers_2},
    )
    assert response.status_code == 201
    assert response.json()["risk_category"] == "Aggressive"

    # Verify GET returns updated values
    response = client.get("/api/v1/risk/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["answers"] == answers_2
    assert data["score"] == 28
    assert data["risk_category"] == "Aggressive"

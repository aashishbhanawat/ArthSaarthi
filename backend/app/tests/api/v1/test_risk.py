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

    # Valid answers representing Growth risk:
    # Q1: B (3), Q2: B (2), Q3: C (3), Q4: C (3), Q5: C (3), Q6: B (2),
    # Q7: B (2), Q8: B (2), Q9: B (3), Q10: B (3), Q11: B (2), Q12: B (2),
    # Q13: B (2) -> Score: 32 (Growth)
    answers = {
        "q1": "B", "q2": "B", "q3": "C", "q4": "C", "q5": "C", "q6": "B",
        "q7": "B", "q8": "B", "q9": "B", "q10": "B", "q11": "B", "q12": "B",
        "q13": "B"
    }

    response = client.post(
        "/api/v1/risk/",
        headers=headers,
        json={"answers": answers},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["answers"] == answers
    assert data["score"] == 32
    assert data["risk_category"] == "Growth"
    assert data["user_id"] == str(user.id)


def test_create_risk_profile_invalid(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    # Missing q13
    answers_missing = {
        "q1": "A", "q2": "A", "q3": "A", "q4": "A", "q5": "A", "q6": "A",
        "q7": "A", "q8": "A", "q9": "A", "q10": "A", "q11": "A", "q12": "A"
    }
    response = client.post(
        "/api/v1/risk/",
        headers=headers,
        json={"answers": answers_missing},
    )
    assert response.status_code == 422

    # Invalid choice "E"
    answers_invalid_choice = {
        "q1": "A", "q2": "A", "q3": "A", "q4": "A", "q5": "A", "q6": "A",
        "q7": "A", "q8": "A", "q9": "A", "q10": "A", "q11": "A", "q12": "A",
        "q13": "E"
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
    # Q1: D (1), Q2-13: A (1) -> Score: 13 (Conservative)
    answers_1 = {
        "q1": "D", "q2": "A", "q3": "A", "q4": "A", "q5": "A", "q6": "A",
        "q7": "A", "q8": "A", "q9": "A", "q10": "A", "q11": "A", "q12": "A",
        "q13": "A"
    }
    response = client.post(
        "/api/v1/risk/",
        headers=headers,
        json={"answers": answers_1},
    )
    assert response.status_code == 201
    assert response.json()["risk_category"] == "Conservative"

    # Update profile: Aggressive
    # Maximum points:
    # Q1: A (4), Q2: D (4), Q3: D (4), Q4: C (3), Q5: C (3), Q6: D (4),
    # Q7: D (4), Q8: D (4), Q9: B (3), Q10: B (3), Q11: D (4), Q12: C (3),
    # Q13: D (4) -> Score: 47 (Aggressive)
    answers_2 = {
        "q1": "A", "q2": "D", "q3": "D", "q4": "C", "q5": "C", "q6": "D",
        "q7": "D", "q8": "D", "q9": "B", "q10": "B", "q11": "D", "q12": "C",
        "q13": "D"
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
    assert data["score"] == 47
    assert data["risk_category"] == "Aggressive"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.user import create_random_user, get_access_token

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")

def test_create_interest_rate(
    client: TestClient, db: Session
) -> None:
    admin_user, admin_password = create_random_user(db, is_admin=True)
    admin_token = get_access_token(client, admin_user.email, admin_password)
    admin_token_headers = {"Authorization": f"Bearer {admin_token}"}

    data = {
        "scheme_name": "PPF",
        "rate": 7.1,
        "start_date": "2023-04-01",
        "end_date": "2023-06-30",
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/interest-rates/",
        headers=admin_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["scheme_name"] == data["scheme_name"]
    assert float(content["rate"]) == data["rate"]
    assert "id" in content


def test_read_interest_rates(
    client: TestClient, db: Session
) -> None:
    admin_user, admin_password = create_random_user(db, is_admin=True)
    admin_token = get_access_token(client, admin_user.email, admin_password)
    admin_token_headers = {"Authorization": f"Bearer {admin_token}"}

    # First create one to ensure there's data
    data = {
        "scheme_name": "NSC",
        "rate": 7.7,
        "start_date": "2023-04-01",
        "end_date": "2023-06-30",
    }
    client.post(
        f"{settings.API_V1_STR}/admin/interest-rates/",
        headers=admin_token_headers,
        json=data,
    )

    response = client.get(
        f"{settings.API_V1_STR}/admin/interest-rates/", headers=admin_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content, list)
    assert len(content) > 0
    assert content[0]["scheme_name"] in ["PPF", "NSC"]


def test_update_interest_rate(
    client: TestClient, db: Session
) -> None:
    admin_user, admin_password = create_random_user(db, is_admin=True)
    admin_token = get_access_token(client, admin_user.email, admin_password)
    admin_token_headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "scheme_name": "KVP",
        "rate": 7.5,
        "start_date": "2023-04-01",
        "end_date": "2023-06-30",
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/interest-rates/",
        headers=admin_token_headers,
        json=data,
    )
    rate_id = response.json()["id"]

    update_data = {
        "scheme_name": "KVP",
        "rate": 7.6,
        "start_date": "2023-04-01",
        "end_date": "2023-06-30",
    }
    response = client.put(
        f"{settings.API_V1_STR}/admin/interest-rates/{rate_id}",
        headers=admin_token_headers,
        json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert float(content["rate"]) == 7.6


def test_delete_interest_rate(
    client: TestClient, db: Session
) -> None:
    admin_user, admin_password = create_random_user(db, is_admin=True)
    admin_token = get_access_token(client, admin_user.email, admin_password)
    admin_token_headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "scheme_name": "SCSS",
        "rate": 8.2,
        "start_date": "2023-04-01",
        "end_date": "2023-06-30",
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/interest-rates/",
        headers=admin_token_headers,
        json=data,
    )
    rate_id = response.json()["id"]

    response = client.delete(
        f"{settings.API_V1_STR}/admin/interest-rates/{rate_id}",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == rate_id


def test_non_admin_cannot_access(
    client: TestClient, db: Session
) -> None:
    normal_user, normal_password = create_random_user(db, is_admin=False)
    normal_user_token = get_access_token(client, normal_user.email, normal_password)
    normal_user_token_headers = {"Authorization": f"Bearer {normal_user_token}"}
    response = client.get(
        f"{settings.API_V1_STR}/admin/interest-rates/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_seed_interest_rates_correctness(db: Session) -> None:
    from datetime import date, timedelta

    from app.db.initial_data import seed_interest_rates
    from app.db.seed_data.ppf_interest_rates import HISTORICAL_PPF_RATES

    # 1. Run validation directly on the HISTORICAL_PPF_RATES list
    assert len(HISTORICAL_PPF_RATES) > 0

    # Check that entries are sorted and have no gaps or overlaps
    for i in range(len(HISTORICAL_PPF_RATES)):
        rate = HISTORICAL_PPF_RATES[i]
        assert rate["start_date"] <= rate["end_date"], (
            f"Start date after end date for rate index {i}"
        )
        assert rate["rate"] >= 0, f"Negative rate at index {i}"

        if i > 0:
            prev_rate = HISTORICAL_PPF_RATES[i - 1]
            expected_start = prev_rate["end_date"] + timedelta(days=1)
            assert rate["start_date"] == expected_start, (
                f"Gap or overlap between index {i - 1} and {i}: "
                f"expected start {expected_start}, got {rate['start_date']}"
            )

    # Verify that the latest rates cover up to 2026-06-30 (Q2-2026)
    last_rate = HISTORICAL_PPF_RATES[-1]
    assert last_rate["end_date"] >= date(2026, 6, 30), (
        f"Seed data does not cover Q2-2026. Got: {last_rate['end_date']}"
    )

    # 2. Test database seeding logic
    seed_interest_rates(db)

    # Retrieve seeded interest rates from database
    from app import crud
    db_rates = crud.historical_interest_rate.get_multi(db, limit=100)
    ppf_db_rates = [r for r in db_rates if r.scheme_name == "PPF"]

    assert len(ppf_db_rates) == len(HISTORICAL_PPF_RATES)

    db_rate_map = {r.start_date: r for r in ppf_db_rates}
    for rate_data in HISTORICAL_PPF_RATES:
        db_record = db_rate_map.get(rate_data["start_date"])
        assert db_record is not None, (
            f"Missing database record for start date {rate_data['start_date']}"
        )
        assert db_record.end_date == rate_data["end_date"]
        assert db_record.rate == rate_data["rate"]



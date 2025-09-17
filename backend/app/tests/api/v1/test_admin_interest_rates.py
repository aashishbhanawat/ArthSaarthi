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

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.user import User
from app.tests.utils.user import create_random_user, get_access_token


def test_get_current_user(client: TestClient, db: Session) -> None:
    user, password = create_random_user(db)
    access_token = get_access_token(client, user.email, password)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert response.status_code == 200
    current_user = User(**response.json())
    assert current_user.email == user.email
    assert current_user.full_name == user.full_name


def test_update_current_user(client: TestClient, db: Session) -> None:
    user, password = create_random_user(db)
    access_token = get_access_token(client, user.email, password)
    headers = {"Authorization": f"Bearer {access_token}"}
    new_full_name = "Updated Name"
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
        json={"full_name": new_full_name},
    )
    assert response.status_code == 200
    updated_user = User(**response.json())
    assert updated_user.email == user.email
    assert updated_user.full_name == new_full_name

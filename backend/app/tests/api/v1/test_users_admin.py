import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.user import User as UserModel
from app.tests.utils.user import (
    create_random_user,
    get_access_token,
    random_email,
)

pytestmark = [
    pytest.mark.usefixtures("pre_unlocked_key_manager"),
    pytest.mark.skipif(
        settings.DEPLOYMENT_MODE == "desktop",
        reason="User management APIs are disabled in desktop mode",
    ),
]


def test_use_access_admin_route(client: TestClient, db: Session) -> None:
    """
    Test access to an admin-only route with a non-admin user.
    """
    user, password = create_random_user(db)
    access_token = get_access_token(client=client, email=user.email, password=password)
    response = client.get(
        "/api/v1/users/",  # Hardcode the correct prefix
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403


def test_use_access_admin_route_admin(client: TestClient, db: Session) -> None:
    """
    Test access to an admin-only route with an admin user.
    """
    user, password = create_random_user(db)
    user.is_admin = True
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = get_access_token(client=client, email=user.email, password=password)

    response = client.get(
        "/api/v1/users/",  # Hardcode the correct prefix
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


def test_create_user_creates_audit_log(client: TestClient, db: Session) -> None:
    """
    Test creating a new user via the admin route creates an audit log.
    """
    admin_user, admin_password = create_random_user(db, is_admin=True)
    admin_access_token = get_access_token(
        client=client, email=admin_user.email, password=admin_password
    )

    user_data = {
        "full_name": "Test User",
        "email": random_email(),
        "password": "ValidPassword123!",
    }

    response = client.post(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json=user_data,
    )

    assert response.status_code == 201
    content = response.json()
    assert content["email"] == user_data["email"]

    log_entry = db.query(AuditLog).filter_by(event_type="USER_CREATED").first()
    assert log_entry is not None
    assert str(log_entry.user_id) == str(admin_user.id)
    assert log_entry.ip_address == "testclient"
    assert str(log_entry.details["created_user_id"]) == content["id"]
    assert log_entry.details["created_user_email"] == user_data["email"]


def test_update_user(client: TestClient, db: Session) -> None:
    """
    Test updating a user's information via the admin route.
    """
    admin_user, admin_password = create_random_user(db, is_admin=True)
    admin_access_token = get_access_token(
        client=client, email=admin_user.email, password=admin_password
    )

    user_to_update, _ = create_random_user(db)
    user_id = user_to_update.id
    update_data = {"full_name": "Updated User", "is_active": False}

    response = client.put(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json=update_data,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(user_id)
    assert content["full_name"] == update_data["full_name"]
    assert content["is_active"] == update_data["is_active"]


def test_delete_user_creates_audit_log(client: TestClient, db: Session) -> None:
    """
    Test deleting a user via the admin route creates an audit log.
    """
    admin_user, admin_password = create_random_user(db, is_admin=True)
    admin_access_token = get_access_token(
        client=client, email=admin_user.email, password=admin_password
    )

    user_to_delete, _ = create_random_user(db)
    user_id_to_delete = user_to_delete.id
    user_email_to_delete = user_to_delete.email

    response = client.delete(
        f"/api/v1/users/{user_id_to_delete}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    assert response.status_code == 200
    deleted_user = db.query(UserModel).filter(UserModel.id == user_id_to_delete).first()
    assert deleted_user is None

    log_entry = db.query(AuditLog).filter_by(event_type="USER_DELETED").first()
    assert log_entry is not None
    assert str(log_entry.user_id) == str(admin_user.id)
    assert log_entry.ip_address == "testclient"
    assert str(log_entry.details["deleted_user_id"]) == str(user_id_to_delete)
    assert log_entry.details["deleted_user_email"] == user_email_to_delete

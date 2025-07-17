import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.user import UserCreate, UserUpdate
from app.tests.utils.user import get_access_token, create_random_user, random_email, random_lower_string
from typing import Any
from app.models.user import User as UserModel

def test_use_access_admin_route(client: TestClient, db: Session) -> None:
    """
    Test access to an admin-only route with a non-admin user.
    """
    user, password = create_random_user(db)
    access_token = get_access_token(client=client, email=user.email, password=password)
    response = client.get(
        "/api/v1/users/",  # Hardcode the correct prefix
        headers={"Authorization": f"Bearer {access_token}"}
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


def test_create_user(client: TestClient, db: Session) -> None:
    """
    Test creating a new user via the admin route.
    """

    admin_user, admin_password = create_random_user(db)
    admin_user.is_admin = True
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    admin_access_token = get_access_token(
        client=client, email=admin_user.email, password=admin_password
    )

    # Define the new user's data
    user_data: dict[str, Any] = {"full_name": "Test User", "email": random_email(), "password": "ValidPassword123!"}

    # Send the request to create the new user
    response = client.post(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json=user_data,
    )

    # Assert the response status and data
    assert response.status_code == 201
    content = response.json()    
    assert content["email"] == user_data["email"]
    assert content["full_name"] == user_data["full_name"]
    assert "id" in content


def test_update_user(client: TestClient, db: Session) -> None:
    """
    Test updating a user's information via the admin route.

    """
    # 1. Create an admin user to authenticate with
    admin_user, admin_password = create_random_user(db)
    admin_user.is_admin = True
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    admin_access_token = get_access_token(
        client=client, email=admin_user.email, password=admin_password)

    # Create a user to update
    user_to_update, _ = create_random_user(db)
    user_id = user_to_update.id

    # Define the update data
    update_data = {"full_name": "Updated User", "is_active": False}

    # Send the request to update the user
    response = client.put(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json=update_data,
    )

    # Assert the response status and data
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == user_id
    assert content["full_name"] == update_data["full_name"]
    assert content["is_active"] == update_data["is_active"]


def test_delete_user(client: TestClient, db: Session) -> None:
    """
    Test deleting a user via the admin route.
    """
    # 1. Create an admin user to authenticate with 
    admin_user, admin_password = create_random_user(db)
    admin_user.is_admin = True
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    admin_access_token = get_access_token(
        client=client, email=admin_user.email, password=admin_password
    )

    #2. Create a user to delete
    user_to_delete, _ = create_random_user(db)
    user_id = user_to_delete.id

    # Send the request to delete the user
    response = client.delete(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    # Assert the response status
    assert response.status_code == 200

    #3. Verify that the user is actually deleted from the database
    deleted_user = db.query(UserModel).filter(UserModel.id == user_id).first()    
    assert deleted_user is None, "User should be deleted from the database"
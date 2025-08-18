import random
import string

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import schemas
from app.core.config import settings
from app.core.security import create_access_token
from app.crud import crud_user


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def create_random_user(db: Session):
    """
    Creates a random user for testing purposes.
    """
    email = random_email()
    # Generate a password that meets the validation criteria
    password_chars = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*()"),
    ]
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    password_chars.extend(random.choices(all_chars, k=8))
    random.shuffle(password_chars)
    password = "".join(password_chars)

    user_in = schemas.user.UserCreate(
        full_name="Test User", email=email, password=password
    )
    user = crud_user.user.create(db, obj_in=user_in)
    return user, password


def get_access_token(client: TestClient, email: str, password: str) -> str:
    if settings.DEPLOYMENT_MODE == "desktop":
        # In desktop mode, for tests not focused on auth, we bypass the login
        # endpoint. This assumes a fixture like `pre_unlocked_key_manager`
        # has already set up and unlocked the master key.
        return create_access_token(subject=email)

    response = client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]

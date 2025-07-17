import random
import string
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas  # Keeping the existing import style for consistency



def create_random_user(db: Session):
    """
    Creates a random user for testing purposes.
    """
    email = "".join(random.choices(string.ascii_lowercase, k=10)) + "@example.com"
    password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
    user_in = schemas.user.UserCreate(full_name="Test User", email=email, password=password)
    user = crud.user.create(db, obj_in=user_in)
    return user, password


def get_access_token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return response.json()["access_token"]
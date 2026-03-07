from app.crud.crud_user import user as user_crud
import pytest
from app.models.user import User

def test_sqli(db):
    try:
        user_crud.get_by_email(db, email="admin@example.com' OR '1'='1")
    except Exception as e:
        print(f"Exception: {e}")

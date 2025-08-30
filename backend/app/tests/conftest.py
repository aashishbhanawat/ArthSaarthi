from typing import Callable, Dict, Generator

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.core import security
from app.core.config import settings
from app.core.key_manager import key_manager
from app.db.base_class import Base
from app.db.session import SessionLocal, engine, get_db
from app.main import app


@pytest.fixture(scope="function")
def pre_unlocked_key_manager(monkeypatch, tmp_path):
    """
    A fixture that prepares the environment for desktop mode testing.
    It points the key manager to a temporary file, generates a key, and
    ensures it is loaded.
    This should be used by any test that performs operations requiring encryption,
    but does not test the key setup/unlocking process itself.
    """
    if settings.DEPLOYMENT_MODE != "desktop":
        yield
        return

    # Create a temporary key file path for the test
    temp_key_path = tmp_path / "test-key.dat"

    # Use monkeypatch to override the hardcoded KEY_FILE_PATH
    monkeypatch.setattr("app.core.key_manager.KEY_FILE_PATH", temp_key_path)

    # This single call generates, wraps, saves, and loads the key.
    key_manager.generate_and_wrap_master_key("testpassword")

    yield key_manager

    # Cleanup: lock the key. The monkeypatch is automatically undone.
    key_manager._master_key = None


@pytest.fixture(scope="session")
def admin_user_data() -> Dict[str, str]:
    return {
        "email": settings.FIRST_SUPERUSER,
        "password": "A-secure-password!123",
        "full_name": "Test Admin",
    }


@pytest.fixture(scope="function")
def get_auth_headers(
    client: TestClient,
) -> Callable[[str, str], Dict[str, str]]:
    def _get_auth_headers(email: str, password: str) -> Dict[str, str]:
        if settings.DEPLOYMENT_MODE == "desktop":
            # In desktop mode, we assume `pre_unlocked_key_manager` has run.
            # We bypass login and directly create a token.
            auth_token = security.create_access_token(subject=email)
        else:
            # In server mode, perform a standard login to get the token.
            login_data = {"username": email, "password": password}
            r = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
            r.raise_for_status()  # Fail fast if login is unsuccessful
            response = r.json()
            auth_token = response["access_token"]

        headers = {"Authorization": f"Bearer {auth_token}"}
        return headers

    return _get_auth_headers





@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Provides a fresh database for each test function.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db_session = SessionLocal()

    yield db_session

    db_session.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Provides a TestClient instance for each test function, with the database
    dependency overridden to use the transactional session from the `db` fixture.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    del app.dependency_overrides[get_db]

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from typing import Generator
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from _pytest.monkeypatch import MonkeyPatch

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.db.base_class import Base
from app.api.deps import get_db


@pytest.fixture(scope="session")
def monkeypatch_session() -> Generator[MonkeyPatch, None, None]:
    """Session-scoped monkeypatch to avoid re-patching for every test."""
    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(monkeypatch_session: MonkeyPatch) -> Generator[None, None, None]:
    """
    Set up the test environment for the entire session.
    This fixture ensures that all tests run in a consistent "desktop" mode
    with a temporary SQLite database and a pre-loaded encryption key.
    """
    from app.core.key_manager import key_manager

    monkeypatch_session.setattr(settings, "DEPLOYMENT_MODE", "desktop")
    monkeypatch_session.setattr(settings, "DATABASE_URL", "sqlite:///:memory:")
    monkeypatch_session.setattr(settings, "ENCRYPTION_KEY_PATH", "test_master.key")
    monkeypatch_session.setattr(settings, "WRAPPED_KEY_PATH", "test_master.key.wrapped")
    monkeypatch_session.setattr(settings, "TEST_MODE", True)

    # The engine is created when db.session is imported. We need to dispose of the
    # old engine and allow a new one to be created with the patched DATABASE_URL.
    engine.dispose()

    # Create all tables for the new in-memory database
    Base.metadata.create_all(bind=engine)

    # In desktop mode, we need a master key for encryption.
    # We generate a dummy key for the test session.
    if settings.DEPLOYMENT_MODE == "desktop":
        key_manager.generate_master_key()
        # Use a dummy password for tests. In a real scenario, this would be derived
        # from the user's password at login.
        key_manager.load_master_key(b"testpassword")

    yield

    # Teardown: Clean up the database and key files
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(settings.ENCRYPTION_KEY_PATH):
        os.remove(settings.ENCRYPTION_KEY_PATH)
    if os.path.exists(settings.WRAPPED_KEY_PATH):
        os.remove(settings.WRAPPED_KEY_PATH)


@pytest.fixture(scope="function")
def db(setup_test_environment: None) -> Generator[Session, None, None]:
    """
    Provides a transactional database session for each test function.
    This fixture ensures that each test runs in a clean, isolated transaction
    that is rolled back at the end, preventing tests from interfering with each other.
    """
    connection = engine.connect()
    transaction = connection.begin()
    db_session = SessionLocal(bind=connection)

    yield db_session

    db_session.close()
    transaction.rollback()
    connection.close()


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

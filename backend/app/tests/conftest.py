import logging
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.tests.utils.user import create_random_user, get_access_token

log = logging.getLogger(__name__)


def get_test_database_url():
    """
    Generates a unique test database URL.
    """
    return str(settings.DATABASE_URL)


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Yields the test database URL.
    """
    yield get_test_database_url()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(test_database_url: str):
    """
    Creates and drops the test database for the test session.
    """
    log.info("*******************************************************************")
    log.info(f"--- Setting up test database: {test_database_url} ---")
    if database_exists(test_database_url):
        log.info("--- Database exists, dropping. ---")
        drop_database(test_database_url)
    create_database(test_database_url)
    log.info("--- Database created successfully. ---")
    yield
    log.info("--- Tearing down test database. ---")
    log.info("*******************************************************************")
    drop_database(test_database_url)


@pytest.fixture(scope="session")
def engine(test_database_url: str):
    """
    Yields a SQLAlchemy engine for the test database.
    """
    log.info("--- Creating Engine ---")
    engine = create_engine(test_database_url)
    yield engine


@pytest.fixture(scope="session")
def TestingSessionLocal(engine):
    """
    Yields a SQLAlchemy session factory for the test database.
    """
    log.info("--- Creating TestingSessionLocal ---")
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables(engine, setup_test_database):
    log.info("--- Creating tables... ---")
    Base.metadata.create_all(bind=engine)
    yield
    log.info("--- Dropping tables... ---")
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    log.info("--- Creating TestClient ---")
    with TestClient(app) as c:
        log.info("--- TestClient is ready ---")
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db(TestingSessionLocal: sessionmaker, engine) -> Generator[Session, None, None]:
    """
    Yields a SQLAlchemy session for the test database.
    """
    log.info("--- Creating Database Session ---")
    connection = engine.connect()  # Get a connection from the engine
    transaction = connection.begin()  # Start a transaction
    session = TestingSessionLocal(bind=connection)  # Bind the session to the connection
    yield session  # Yield the session to the test
    session.close()  # Close the session
    transaction.rollback()  # Rollback the transaction, undoing changes
    connection.close()  # Return the connection to the pool


@pytest.fixture
def admin_user_data() -> dict:
    return {
        "full_name": "Admin User",
        "email": "admin@example.com",
        "password": "ValidPassword123!",
    }


@pytest.fixture
def get_auth_headers(client: TestClient):
    """
    Returns authentication headers for a given email and password.
    """

    def _get_auth_headers(email: str, password: str) -> dict[str, str]:
        log.info(f"--- Getting auth headers for user: {email} ---")
        return {"Authorization": f"Bearer {get_access_token(client, email, password)}"}

    return _get_auth_headers


@pytest.fixture
def superuser_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    admin_user, admin_password = create_random_user(db)
    admin_user.is_admin = True
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    token = get_access_token(client, admin_user.email, admin_password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    user, password = create_random_user(db)
    return {"Authorization": f"Bearer {get_access_token(client, user.email, password)}"}

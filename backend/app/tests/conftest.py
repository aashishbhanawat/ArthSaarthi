import pytest
from typing import Generator
from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal, engine, get_db
from app.db.base_class import Base

@pytest.fixture(scope="session", autouse=True)
def create_test_database() -> Generator[None, None, None]:
    """
    Create a test database for the duration of the test session.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(create_test_database: None) -> Generator[Session, None, None]:
    """
    Provides a transactional database session for each test function.
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

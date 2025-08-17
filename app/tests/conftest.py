import pytest
from typing import Generator, Dict, Callable
from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal, engine, get_db
from app.db.base_class import Base
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate


@pytest.fixture(scope="session")
def admin_user_data() -> Dict[str, str]:
    return {
        "email": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
        "full_name": "Test Admin",
    }


@pytest.fixture(scope="function")
def get_auth_headers(
    client: TestClient, db: Session, admin_user_data: Dict[str, str]
) -> Callable[[str, str], Dict[str, str]]:
    user = crud_user.get_by_email(db, email=admin_user_data["email"])
    if not user:
        user_in = UserCreate(**admin_user_data)
        crud_user.create(db, obj_in=user_in)

    def _get_auth_headers(email: str, password: str) -> Dict[str, str]:
        login_data = {"username": email, "password": password}
        r = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
        response = r.json()
        auth_token = response["access_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}
        return headers

    return _get_auth_headers


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

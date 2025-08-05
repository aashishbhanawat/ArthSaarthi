import io
import uuid
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
from typing import Callable, Dict

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app import models
from app.core.config import settings
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.portfolio import PortfolioCreate
from app.tests.utils.user import create_random_user

@pytest.fixture(scope="function")
def normal_user(db: Session) -> tuple[User, str]:
    """Fixture to create a normal user and return the user object and password."""
    return create_random_user(db)


@pytest.fixture(scope="function")
def other_user(db: Session) -> tuple[User, str]:
    """Fixture to create another normal user."""
    return create_random_user(db)


@pytest.fixture(scope="function")
def user_portfolio(db: Session, normal_user: tuple[User, str]) -> Portfolio:
    """Fixture to create a portfolio for the normal user."""
    user, _ = normal_user
    portfolio_in = PortfolioCreate(name="Test Portfolio", description="A test portfolio")
    portfolio = crud.portfolio.create_with_owner(db=db, obj_in=portfolio_in, user_id=user.id)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@pytest.fixture(scope="function")
def test_asset(db: Session) -> models.Asset:
    """Fixture to create a pre-seeded asset for testing commits."""
    asset_in = models.Asset(
        ticker_symbol="TEST",
        name="Test Asset",
        asset_type="STOCK",
        currency="USD",
        exchange="NASDAQ"
    )
    db.add(asset_in)
    db.commit()
    db.refresh(asset_in)
    return asset_in


@pytest.fixture(scope="function")
def parsed_import_session(
    db: Session, normal_user: tuple[User, str], user_portfolio: Portfolio, test_asset: models.Asset
) -> models.ImportSession:
    """Fixture to create a valid, parsed import session in the DB with a real Parquet file."""
    user, _ = normal_user
    upload_dir = Path(settings.IMPORT_UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    
    df = pd.DataFrame([{"ticker_symbol": test_asset.ticker_symbol, "transaction_type": "BUY", "quantity": 100.0, "price_per_unit": 150.0, "transaction_date": datetime.now(timezone.utc).isoformat(), "fees": 5.0}])
    parsed_file_path = upload_dir / f"{uuid.uuid4()}.parquet"
    df.to_parquet(parsed_file_path)

    session_in = models.ImportSession(user_id=user.id, portfolio_id=user_portfolio.id, file_name="commit_test.csv", file_path="/tmp/dummy.csv", status="PARSED", parsed_file_path=str(parsed_file_path))
    db.add(session_in)
    db.commit()
    db.refresh(session_in)
    return session_in


def create_dummy_csv_file(content: str) -> io.BytesIO:
    """Creates an in-memory CSV file for testing uploads."""
    csv_file = io.BytesIO(content.encode('utf-8'))
    return csv_file


def test_create_import_session(
    client: TestClient,
    db: Session,
    normal_user: tuple[User, str],
    user_portfolio: Portfolio,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)
    csv_content = "ticker_symbol,transaction_type,quantity,price_per_unit,transaction_date\nTEST,BUY,10,100.0,2023-01-01"
    csv_file = create_dummy_csv_file(csv_content)

    response = client.post(
        "/api/v1/import-sessions/",
        data={"portfolio_id": str(user_portfolio.id)},
        files={"file": ("test.csv", csv_file, "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_name"] == "test.csv"
    assert data["status"] == "PARSED"
    assert data["portfolio_id"] == str(user_portfolio.id)
    assert data["user_id"] == str(user.id)
    assert Path(data["file_path"]).exists()
    assert Path(data["parsed_file_path"]).exists()

    # Clean up created files
    Path(data["file_path"]).unlink()
    Path(data["parsed_file_path"]).unlink()


def test_create_import_session_unauthorized(
    client: TestClient,
    db: Session,
    other_user: tuple[User, str],
    user_portfolio: Portfolio, # Belongs to normal_user
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = other_user
    auth_headers = get_auth_headers(user.email, password)
    csv_content = "ticker_symbol,transaction_type,quantity,price_per_unit,transaction_date\nTEST,BUY,10,100.0,2023-01-01"
    csv_file = create_dummy_csv_file(csv_content)

    response = client.post(
        "/api/v1/import-sessions/",
        data={"portfolio_id": str(user_portfolio.id)},
        files={"file": ("test.csv", csv_file, "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 403
    assert "Not enough permissions" in response.json()["detail"]


def test_create_import_session_empty_file(
    client: TestClient,
    db: Session,
    normal_user: tuple[User, str],
    user_portfolio: Portfolio,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)
    csv_file = create_dummy_csv_file("") # Empty content

    response = client.post(
        "/api/v1/import-sessions/",
        data={"portfolio_id": str(user_portfolio.id)},
        files={"file": ("empty.csv", csv_file, "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Failed to parse file" in response.json()["detail"]


def test_get_import_session_preview(
    client: TestClient,
    db: Session,
    normal_user: tuple[User, str],
    parsed_import_session: models.ImportSession,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)

    response = client.get(
        f"/api/v1/import-sessions/{parsed_import_session.id}/preview",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["ticker_symbol"] == "TEST"


def test_get_import_session_preview_unauthorized(
    client: TestClient,
    db: Session,
    other_user: tuple[User, str],
    parsed_import_session: models.ImportSession, # Belongs to normal_user
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = other_user
    auth_headers = get_auth_headers(user.email, password)

    response = client.get(
        f"/api/v1/import-sessions/{parsed_import_session.id}/preview",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_commit_import_session_success(
    client: TestClient,
    db: Session,
    normal_user: tuple[User, str],
    parsed_import_session: models.ImportSession,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)

    response = client.post(
        f"/api/v1/import-sessions/{parsed_import_session.id}/commit",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "Successfully committed 1 transactions" in response.json()["msg"]

    # Verify the transaction was created
    transactions = crud.transaction.get_multi_by_portfolio(db, portfolio_id=parsed_import_session.portfolio_id)
    assert len(transactions) == 1
    assert transactions[0].asset.ticker_symbol == "TEST"
    assert transactions[0].quantity == Decimal("100.0")

    # Verify the session status was updated
    db.refresh(parsed_import_session)
    assert parsed_import_session.status == "COMPLETED"


def test_commit_import_session_asset_not_found(
    client: TestClient,
    db: Session,
    normal_user: tuple[User, str],
    user_portfolio: Portfolio,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)

    # Create a session with a parquet file that references a non-existent asset
    upload_dir = Path(settings.IMPORT_UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    df = pd.DataFrame([{"ticker_symbol": "NONEXISTENT", "transaction_type": "BUY", "quantity": 10, "price_per_unit": 100, "transaction_date": "2023-01-01", "fees": 0}])
    parsed_file_path = upload_dir / f"{uuid.uuid4()}.parquet"
    df.to_parquet(parsed_file_path)
    session_in = models.ImportSession(user_id=user.id, portfolio_id=user_portfolio.id, file_name="bad_asset.csv", file_path="/tmp/dummy.csv", status="PARSED", parsed_file_path=str(parsed_file_path))
    db.add(session_in)
    db.commit()
    db.refresh(session_in)

    response = client.post(
        f"/api/v1/import-sessions/{session_in.id}/commit",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Asset with ticker 'NONEXISTENT' not found" in response.json()["detail"]

    # Verify session status is FAILED
    db.refresh(session_in)
    assert session_in.status == "FAILED"


def test_commit_import_session_wrong_status(
    client: TestClient,
    db: Session,
    normal_user: tuple[User, str],
    user_portfolio: Portfolio,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)
    # Create a session with UPLOADED status, not PARSED
    session_in = models.ImportSession(user_id=user.id, portfolio_id=user_portfolio.id, file_name="test.csv", file_path="/tmp/dummy.csv", status="UPLOADED")
    db.add(session_in)
    db.commit()
    db.refresh(session_in)

    response = client.post(
        f"/api/v1/import-sessions/{session_in.id}/commit",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Cannot commit session with status 'UPLOADED'" in response.json()["detail"]


def test_commit_import_session_unauthorized(
    client: TestClient,
    db: Session,
    other_user: tuple[User, str],
    parsed_import_session: models.ImportSession, # Belongs to normal_user
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = other_user
    auth_headers = get_auth_headers(user.email, password)

    response = client.post(
        f"/api/v1/import-sessions/{parsed_import_session.id}/commit",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_commit_import_session_missing_columns(
    client: TestClient,
    db: Session,
    normal_user: tuple[User, str],
    user_portfolio: Portfolio,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)

    # Create a session with a parquet file that is missing a required column
    upload_dir = Path(settings.IMPORT_UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    df = pd.DataFrame([{"ticker_symbol": "TEST", "quantity": 10}]) # Missing transaction_type, etc.
    parsed_file_path = upload_dir / f"{uuid.uuid4()}.parquet"
    df.to_parquet(parsed_file_path)
    session_in = models.ImportSession(user_id=user.id, portfolio_id=user_portfolio.id, file_name="bad_cols.csv", file_path="/tmp/dummy.csv", status="PARSED", parsed_file_path=str(parsed_file_path))
    db.add(session_in)
    db.commit()
    db.refresh(session_in)

    response = client.post(
        f"/api/v1/import-sessions/{session_in.id}/commit",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Parsed file is missing required columns" in response.json()["detail"]
    

import io
import uuid
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone

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
    # Create a user to be used in the tests
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
    return crud.portfolio.create_with_owner(db=db, obj_in=portfolio_in, user_id=user.id)


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
    return io.BytesIO(content.encode("utf-8"))


def test_create_import_session(
    client: TestClient,
    get_auth_headers,
    normal_user: tuple[User, str],
    user_portfolio: Portfolio,
) -> None:
    """
    Test creating a new import session successfully.
    """
    csv_content = "col1,col2\n1,3\n2,4"
    user, password = normal_user
    normal_user_token_headers = get_auth_headers(user.email, password)
    dummy_file = create_dummy_csv_file(csv_content)

    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/",
        headers=normal_user_token_headers,
        data={"portfolio_id": str(user_portfolio.id)},
        files={"file": ("test.csv", dummy_file, "text/csv")},
    )

    assert response.status_code == 201, response.text
    content = response.json()
    assert content["file_name"] == "test.csv"
    assert content["status"] == "PARSED"
    assert "id" in content
    assert "parsed_file_path" in content
    assert content["parsed_file_path"] is not None
    assert Path(content["parsed_file_path"]).exists()

    # Verify the content of the parsed file
    expected_df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    parsed_df = pd.read_parquet(content["parsed_file_path"])
    pd.testing.assert_frame_equal(parsed_df, expected_df)


def test_create_import_session_portfolio_not_found(
    client: TestClient,
    get_auth_headers,
    normal_user: tuple[User, str],
) -> None:
    """
    Test creating an import session for a non-existent portfolio.
    """
    non_existent_uuid = uuid.uuid4()
    user, password = normal_user
    normal_user_token_headers = get_auth_headers(user.email, password)
    csv_content = "col1,col2\n1,3"
    dummy_file = create_dummy_csv_file(csv_content)

    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/",
        headers=normal_user_token_headers,
        data={"portfolio_id": str(non_existent_uuid)},
        files={"file": ("test.csv", dummy_file, "text/csv")},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Portfolio not found"


def test_create_import_session_not_enough_permissions(
    client: TestClient,
    get_auth_headers,
    other_user: tuple[User, str],
    user_portfolio: Portfolio,  # Belongs to normal_user
) -> None:
    """
    Test creating an import session for a portfolio the user does not own.
    """
    csv_content = "col1,col2\n1,3"
    other_user_obj, other_user_password = other_user
    other_user_token_headers = get_auth_headers(other_user_obj.email, other_user_password)
    dummy_file = create_dummy_csv_file(csv_content)

    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/",
        headers=other_user_token_headers,
        data={"portfolio_id": str(user_portfolio.id)},
        files={"file": ("test.csv", dummy_file, "text/csv")},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions for this portfolio"


def test_get_import_session_preview(
    client: TestClient,
    get_auth_headers,
    normal_user: tuple[User, str],
    user_portfolio: Portfolio,
) -> None:
    """
    Test getting a preview of a successfully parsed import session.
    """
    # First, create an import session
    user, password = normal_user
    normal_user_token_headers = get_auth_headers(user.email, password)
    csv_content = "col1,col2\n1,3\n2,4"
    dummy_file = create_dummy_csv_file(csv_content)
    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/",
        headers=normal_user_token_headers,
        data={"portfolio_id": str(user_portfolio.id)},
        files={"file": ("test.csv", dummy_file, "text/csv")},
    )
    assert response.status_code == 201
    session_id = response.json()["id"]

    # Now, get the preview
    response = client.get(
        f"{settings.API_V1_STR}/import-sessions/{session_id}/preview",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 200
    preview_data = response.json()
    expected_data = [{"col1": 1, "col2": 3}, {"col1": 2, "col2": 4}]
    assert preview_data == expected_data


def test_get_import_session_preview_not_found(
    client: TestClient,
    get_auth_headers,
    normal_user: tuple[User, str],
) -> None:
    """
    Test getting a preview for a non-existent session ID.
    """
    user, password = normal_user
    normal_user_token_headers = get_auth_headers(user.email, password)
    non_existent_uuid = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/import-sessions/{non_existent_uuid}/preview",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404


def test_get_import_session_preview_not_enough_permissions(
    client: TestClient,
    get_auth_headers,
    normal_user: tuple[User, str],
    other_user: tuple[User, str],
    user_portfolio: Portfolio,  # Belongs to normal_user
) -> None:
    """
    Test that a user cannot get a preview for a session they do not own.
    """
    # Create a session with normal_user
    user, password = normal_user
    normal_user_token_headers = get_auth_headers(user.email, password)
    csv_content = "col1,col2\n1,3\n2,4"
    dummy_file = create_dummy_csv_file(csv_content)
    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/",
        headers=normal_user_token_headers,
        data={"portfolio_id": str(user_portfolio.id)},
        files={"file": ("test.csv", dummy_file, "text/csv")},
    )
    assert response.status_code == 201
    session_id = response.json()["id"]

    # Try to access it with other_user
    other_user_obj, other_user_password = other_user
    other_user_token_headers = get_auth_headers(other_user_obj.email, other_user_password)
    response = client.get(
        f"{settings.API_V1_STR}/import-sessions/{session_id}/preview",
        headers=other_user_token_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


# --- Tests for Commit Endpoint ---

def test_commit_import_session_success(
    client: TestClient,
    get_auth_headers,
    db: Session,
    normal_user: tuple[User, str],
    user_portfolio: Portfolio,
    parsed_import_session: models.ImportSession,
) -> None:
    """
    Test successfully committing a parsed import session.
    """
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)

    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/{parsed_import_session.id}/commit",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"msg": "Successfully committed 1 transactions."}

    # Verify the session status is updated in the DB
    db.refresh(parsed_import_session)
    assert parsed_import_session.status == "COMPLETED"

    # Verify the transaction was created
    transactions = crud.transaction.get_multi_by_portfolio(db, portfolio_id=user_portfolio.id)
    assert len(transactions) == 1
    assert transactions[0].quantity == Decimal("100.0")
    assert transactions[0].price_per_unit == Decimal("150.0")


def test_commit_import_session_not_found(client: TestClient, get_auth_headers, normal_user: tuple[User, str]) -> None:
    """
    Test committing a session that does not exist.
    """
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)
    non_existent_uuid = uuid.uuid4()
    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/{non_existent_uuid}/commit",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_commit_import_session_not_enough_permissions(
    client: TestClient, get_auth_headers, other_user: tuple[User, str], parsed_import_session: models.ImportSession
) -> None:
    """
    Test a user trying to commit a session they do not own.
    """
    other_user_obj, other_user_password = other_user
    auth_headers = get_auth_headers(other_user_obj.email, other_user_password)
    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/{parsed_import_session.id}/commit",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_commit_import_session_invalid_status(
    client: TestClient, get_auth_headers, db: Session, normal_user: tuple[User, str], user_portfolio: Portfolio
) -> None:
    """
    Test committing a session that is not in the 'PARSED' state.
    """
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)
    
    session_in = models.ImportSession(user_id=user.id, portfolio_id=user_portfolio.id, file_name="test.csv", file_path="/tmp/dummy", status="UPLOADED")
    db.add(session_in)
    db.commit()

    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/{session_in.id}/commit",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Cannot commit session with status 'UPLOADED'" in response.json()["detail"]


def test_commit_import_session_asset_not_found(
    client: TestClient, get_auth_headers, db: Session, normal_user: tuple[User, str], user_portfolio: Portfolio
) -> None:
    """
    Test committing a session where an asset in the file does not exist in the database.
    """
    user, password = normal_user
    auth_headers = get_auth_headers(user.email, password)

    # Create a parsed session with a file containing an unknown ticker
    upload_dir = Path(settings.IMPORT_UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    df = pd.DataFrame([{"ticker_symbol": "UNKNOWN", "transaction_type": "BUY", "quantity": 100.0, "price_per_unit": 150.0, "transaction_date": datetime.now(timezone.utc).isoformat(), "fees": 0.0}])
    parsed_file_path = upload_dir / f"{uuid.uuid4()}.parquet"
    df.to_parquet(parsed_file_path)
    session_in = models.ImportSession(user_id=user.id, portfolio_id=user_portfolio.id, file_name="test.csv", file_path="/tmp/dummy", status="PARSED", parsed_file_path=str(parsed_file_path))
    db.add(session_in)
    db.commit()

    response = client.post(
        f"{settings.API_V1_STR}/import-sessions/{session_in.id}/commit",
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "Asset with ticker 'UNKNOWN' not found" in response.json()["detail"]

    # Verify the session status was updated to FAILED
    db.refresh(session_in)
    assert session_in.status == "FAILED"
    assert "Asset with ticker 'UNKNOWN' not found" in session_in.error_message

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.crud import user as crud_user
from app.schemas import UserCreate
from app.tests.utils.user import create_random_user





@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    # Create a user to be used in the tests
    user, _ = create_random_user(db)
    return user


def test_create_import_session(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    # Create a dummy CSV file
    test_data = {"col1": [1, 2], "col2": [3, 4]}
    df = pd.DataFrame(test_data)
    df.to_csv("test.csv", index=False)

    with open("test.csv", "rb") as f:
        response = client.post(
            f"{settings.API_V1_STR}/import-sessions/",
            headers=superuser_token_headers,
            files={"file": ("test.csv", f, "text/csv")},
        )

    assert response.status_code == 201
    content = response.json()
    assert content["file_name"] == "test.csv"
    assert content["status"] == "PARSED"
    assert "id" in content
    assert "parsed_file_path" in content
    assert content["parsed_file_path"] is not None

    # Verify the content of the parsed file
    parsed_df = pd.read_parquet(content["parsed_file_path"])
    pd.testing.assert_frame_equal(parsed_df, df)


def test_get_import_session_preview(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    # First, create an import session
    test_data = {"col1": [1, 2], "col2": [3, 4]}
    df = pd.DataFrame(test_data)
    df.to_csv("test.csv", index=False)

    with open("test.csv", "rb") as f:
        response = client.post(
            f"{settings.API_V1_STR}/import-sessions/",
            headers=superuser_token_headers,
            files={"file": ("test.csv", f, "text/csv")},
        )
    session_id = response.json()["id"]

    # Now, get the preview
    response = client.get(
        f"{settings.API_V1_STR}/import-sessions/{session_id}/preview",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    preview_data = response.json()
    assert preview_data == pd.DataFrame(test_data).to_dict(orient="records")


import uuid

def test_get_import_session_preview_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    non_existent_uuid = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/import-sessions/{non_existent_uuid}/preview",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_get_import_session_preview_not_enough_permissions(
    client: TestClient,
    db: Session,
    test_user: User,
    test_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    # Create a session with one user
    test_data = {"col1": [1, 2], "col2": [3, 4]}
    df = pd.DataFrame(test_data)
    df.to_csv("test.csv", index=False)

    with open("test.csv", "rb") as f:
        response = client.post(
            f"{settings.API_V1_STR}/import-sessions/",
            headers=test_user_token_headers, # Use the test user's token
            files={"file": ("test.csv", f, "text/csv")},
        )
    session_id = response.json()["id"]

    # Try to access it with the superuser
    response = client.get(
        f"{settings.API_V1_STR}/import-sessions/{session_id}/preview",
        headers=superuser_token_headers, # Use the superuser's token
    )
    assert response.status_code == 403

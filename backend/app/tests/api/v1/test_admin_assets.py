import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.asset import create_test_asset
from app.tests.utils.user import create_random_user, get_access_token

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")

API_PREFIX = f"{settings.API_V1_STR}/admin/assets"


def _admin_headers(client: TestClient, db: Session) -> dict:
    """Helper to create an admin user and return auth headers."""
    admin_user, admin_password = create_random_user(db, is_admin=True)
    token = get_access_token(client, admin_user.email, admin_password)
    return {"Authorization": f"Bearer {token}"}


def test_search_local_assets_general(client: TestClient, db: Session) -> None:
    """Test general asset search endpoint."""
    headers = _admin_headers(client, db)

    # Create test assets
    # Create test assets
    create_test_asset(db, ticker_symbol="SRCHTEST1", name="Search Asset One")
    create_test_asset(db, ticker_symbol="SRCHTEST2", name="Search Asset Two")
    db.commit()

    # Search by ticker
    response = client.get(
        f"{API_PREFIX}/search-local",
        headers=headers,
        params={"query": "SRCHTEST1"}
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert content[0]["ticker_symbol"] == "SRCHTEST1"

    # Search by name
    response = client.get(
        f"{API_PREFIX}/search-local",
        headers=headers,
        params={"query": "Asset Two"}
    )
    assert response.status_code == 200
    content = response.json()
    found = False
    for asset in content:
        if asset["ticker_symbol"] == "SRCHTEST2":
            found = True
            break
    assert found

    # Search with no query (should return list)
    response = client.get(
        f"{API_PREFIX}/search-local",
        headers=headers
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_local_assets_requires_auth(client: TestClient) -> None:
    """Test that auth is required."""
    response = client.get(f"{API_PREFIX}/search-local")
    assert response.status_code == 401

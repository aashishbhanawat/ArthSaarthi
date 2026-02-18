"""
API tests for admin alias endpoints.
Tests CRUD operations and non-admin access denial.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.asset import create_test_asset
from app.tests.utils.user import create_random_user, get_access_token

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")

API_PREFIX = f"{settings.API_V1_STR}/admin/aliases"


def _admin_headers(client: TestClient, db: Session) -> dict:
    """Helper to create an admin user and return auth headers."""
    admin_user, admin_password = create_random_user(db, is_admin=True)
    token = get_access_token(client, admin_user.email, admin_password)
    return {"Authorization": f"Bearer {token}"}


def test_create_alias(client: TestClient, db: Session) -> None:
    """Test creating a new symbol alias via the API."""
    headers = _admin_headers(client, db)
    asset = create_test_asset(db, ticker_symbol="TESTALIAS1", name="Test Alias Asset")
    db.commit()

    data = {
        "alias_symbol": "MYALIAS",
        "source": "Zerodha Tradebook",
        "asset_id": str(asset.id),
    }
    response = client.post(f"{API_PREFIX}/", headers=headers, json=data)
    assert response.status_code == 201
    content = response.json()
    assert content["alias_symbol"] == "MYALIAS"
    assert content["source"] == "Zerodha Tradebook"
    assert content["asset_id"] == str(asset.id)
    assert "id" in content


def test_list_aliases(client: TestClient, db: Session) -> None:
    """Test listing all aliases returns created alias with asset info."""
    headers = _admin_headers(client, db)
    asset = create_test_asset(db, ticker_symbol="LISTTEST", name="List Test Asset")
    db.commit()

    # Create an alias first
    client.post(
        f"{API_PREFIX}/",
        headers=headers,
        json={
            "alias_symbol": "LISTALIAS",
            "source": "Test Source",
            "asset_id": str(asset.id),
        },
    )

    response = client.get(f"{API_PREFIX}/", headers=headers)
    assert response.status_code == 200
    content = response.json()
    assert "items" in content
    assert "total" in content
    assert content["total"] > 0
    # Find our created alias
    our_alias = [a for a in content["items"] if a["alias_symbol"] == "LISTALIAS"]
    assert len(our_alias) == 1
    assert our_alias[0]["asset_name"] == "List Test Asset"
    assert our_alias[0]["asset_ticker"] == "LISTTEST"


def test_update_alias(client: TestClient, db: Session) -> None:
    """Test updating an alias changes its fields."""
    headers = _admin_headers(client, db)
    asset1 = create_test_asset(db, ticker_symbol="UPDASSET1", name="First Asset")
    asset2 = create_test_asset(db, ticker_symbol="UPDASSET2", name="Second Asset")
    db.commit()

    # Create an alias
    response = client.post(
        f"{API_PREFIX}/",
        headers=headers,
        json={
            "alias_symbol": "OLDALIAS",
            "source": "Old Source",
            "asset_id": str(asset1.id),
        },
    )
    alias_id = response.json()["id"]

    # Update it
    update_data = {
        "alias_symbol": "NEWALIAS",
        "source": "New Source",
        "asset_id": str(asset2.id),
    }
    response = client.put(
        f"{API_PREFIX}/{alias_id}", headers=headers, json=update_data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["alias_symbol"] == "NEWALIAS"
    assert content["source"] == "New Source"
    assert content["asset_id"] == str(asset2.id)


def test_delete_alias(client: TestClient, db: Session) -> None:
    """Test deleting an alias removes it."""
    headers = _admin_headers(client, db)
    asset = create_test_asset(db, ticker_symbol="DELTEST", name="Delete Test")
    db.commit()

    # Create
    response = client.post(
        f"{API_PREFIX}/",
        headers=headers,
        json={
            "alias_symbol": "DELALIAS",
            "source": "Test",
            "asset_id": str(asset.id),
        },
    )
    alias_id = response.json()["id"]

    # Delete
    response = client.delete(f"{API_PREFIX}/{alias_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["msg"] == "Alias deleted successfully."

    # Verify it's gone from the list
    response = client.get(f"{API_PREFIX}/", headers=headers)
    ids = [a["id"] for a in response.json()["items"]]
    assert alias_id not in ids


def test_search_aliases(client: TestClient, db: Session) -> None:
    """Test that search query filters aliases by alias_symbol."""
    headers = _admin_headers(client, db)
    asset = create_test_asset(
        db, ticker_symbol="SRCHTEST", name="Search Test Asset"
    )
    db.commit()

    client.post(
        f"{API_PREFIX}/",
        headers=headers,
        json={
            "alias_symbol": "XYZUNIQUE",
            "source": "Test",
            "asset_id": str(asset.id),
        },
    )

    # Search should find it
    response = client.get(
        f"{API_PREFIX}/", headers=headers, params={"q": "XYZUNIQUE"}
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1
    syms = [a["alias_symbol"] for a in response.json()["items"]]
    assert "XYZUNIQUE" in syms

    # Search with non-matching query should return 0
    response = client.get(
        f"{API_PREFIX}/", headers=headers, params={"q": "ZZZNOMATCH"}
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_create_duplicate_alias_rejected(client: TestClient, db: Session) -> None:
    """Test that creating a duplicate alias_symbol+source is rejected."""
    headers = _admin_headers(client, db)
    asset = create_test_asset(db, ticker_symbol="DUPTEST", name="Dup Test")
    db.commit()

    data = {
        "alias_symbol": "DUPALIAS",
        "source": "Same Source",
        "asset_id": str(asset.id),
    }
    response = client.post(f"{API_PREFIX}/", headers=headers, json=data)
    assert response.status_code == 201

    # Try creating the same one again
    response = client.post(f"{API_PREFIX}/", headers=headers, json=data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_non_admin_cannot_access(client: TestClient, db: Session) -> None:
    """Test that non-admin users get 403 on alias endpoints."""
    user, password = create_random_user(db, is_admin=False)
    token = get_access_token(client, user.email, password)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"{API_PREFIX}/", headers=headers)
    assert response.status_code == 403

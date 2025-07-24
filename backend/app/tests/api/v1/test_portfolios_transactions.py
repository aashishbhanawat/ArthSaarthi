import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.config import settings
from app.tests.utils.user import create_random_user
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.tests.utils.asset import create_test_asset
from app import crud, schemas
from app.models.asset import Asset


def test_create_portfolio(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    data = {"name": "Test Portfolio", "description": "A test portfolio"}
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert content["user_id"] == user.id


def test_read_portfolios(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    create_test_portfolio(db, user_id=user.id, name="Portfolio 1")
    create_test_portfolio(db, user_id=user.id, name="Portfolio 2")
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 2


def test_read_portfolio_by_id(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="My Portfolio")
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == portfolio.name
    assert content["id"] == portfolio.id


def test_read_portfolio_wrong_owner(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    other_user, _ = create_random_user(db) # We don't need the other user's password
    portfolio = create_test_portfolio(db, user_id=other_user.id, name="Other's Portfolio")
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_delete_portfolio(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="To Be Deleted")
    response = client.delete(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    deleted_portfolio = crud.portfolio.get(db, id=portfolio.id)
    assert deleted_portfolio is None


def test_lookup_asset(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """Tests that asset lookup returns a list of matching assets."""
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    create_test_asset(db, ticker_symbol="AAPL")
    response = client.get(
        f"{settings.API_V1_STR}/assets/lookup/?query=AAPL",
        headers=auth_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content, list)
    assert len(content) == 1
    assert content[0]["ticker_symbol"] == "AAPL"
    assert content[0]["name"] == "AAPL Company"


def test_lookup_asset_not_found(
    client: TestClient, db: Session, get_auth_headers, mocker
) -> None:
    """
    Tests that asset lookup returns an empty list for a non-existent asset
    both locally and externally.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    # Mock local DB search to find nothing
    mocker.patch("app.crud.asset.search_by_name_or_ticker", return_value=[])

    # Mock external service to find nothing
    mocker.patch(
        "app.services.financial_data_service.financial_data_service.get_asset_details",
        return_value=None,
    )

    response = client.get(
        f"{settings.API_V1_STR}/assets/lookup/?query=UNKNOWNTICKER",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


def test_create_transaction_with_new_asset(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="My Portfolio")
    data = {
        "new_asset": {
            "ticker_symbol": "MSFT",
            "name": "Microsoft Corp",
            "asset_type": "STOCK",
                "currency": "USD",
                "exchange": "NASDAQ",
        },
        "transaction_type": "BUY",
        "quantity": 10,
        "price_per_unit": 300.50,
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/transactions/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert float(content["quantity"]) == 10.0
    assert content["asset"]["ticker_symbol"] == "MSFT"

    # Verify asset was created in DB
    asset_in_db = crud.asset.get_by_ticker(db, ticker_symbol="MSFT")
    assert asset_in_db is not None
    assert asset_in_db.name == "Microsoft Corp"


def test_create_transaction_with_existing_asset(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="My Portfolio")
    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            ticker_symbol="TSLA",
            name="Tesla Inc.",
            asset_type="Stock",
            currency="USD",
            exchange="NASDAQ",
        ),
    )
    data = {
        "asset_id": asset.id,
        "transaction_type": "BUY",
        "quantity": 5,
        "price_per_unit": 250.00,
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/transactions/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["asset"]["id"] == asset.id


def test_create_transaction_for_other_user_portfolio(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    other_user, _ = create_random_user(db) # We don't need the other user's password
    portfolio = create_test_portfolio(db, user_id=other_user.id, name="Other's Portfolio")
    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            ticker_symbol="AMZN",
            name="Amazon.com Inc.",
            asset_type="Stock",
            currency="USD",
            exchange="NASDAQ",
        ),
    )
    data = {
        "asset_id": asset.id,
        "transaction_type": "BUY",
        "quantity": 2,
        "price_per_unit": 130.00,
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/transactions/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 403


def test_create_transaction_conflicting_asset_info(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="My Portfolio")
    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            ticker_symbol="NVDA",
            name="NVIDIA Corp",
            asset_type="Stock",
            currency="USD",
            exchange="NASDAQ",
        ),
    )
    data = {
        "asset_id": asset.id, # Providing both asset_id
        "new_asset": {
            "ticker_symbol": "NVDA",
            "name": "NVIDIA Corp",
            "asset_type": "STOCK",
            "currency": "USD",
            "exchange": "NASDAQ",
        }, # and new_asset
        "transaction_type": "BUY",
        "quantity": 10,
        "price_per_unit": 450.00,
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/transactions/",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 422


def test_read_assets(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """
    Test retrieving all assets.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    create_test_asset(db, ticker_symbol="ASSET1")
    create_test_asset(db, ticker_symbol="ASSET2")

    response = client.get(
        f"{settings.API_V1_STR}/assets/", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_read_asset_by_id(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """
    Test retrieving a specific asset by its ID.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    asset = create_test_asset(db, ticker_symbol="TESTASSET")

    response = client.get(
        f"{settings.API_V1_STR}/assets/{asset.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ticker_symbol"] == "TESTASSET"
    assert data["id"] == asset.id


def test_read_asset_by_id_not_found(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    """Test retrieving a non-existent asset by ID returns 404."""
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)
    response = client.get(f"{settings.API_V1_STR}/assets/999999", headers=auth_headers)
    assert response.status_code == 404


def test_lookup_asset_external_and_create(
    client: TestClient, db: Session, get_auth_headers, mocker
) -> None:
    """
    Tests that asset lookup queries an external service if not found locally
    and creates the asset in the local database.
    """
    user, password = create_random_user(db)
    auth_headers = get_auth_headers(user.email, password)

    # 1. Mock local DB search to find nothing
    mocker.patch("app.crud.asset.search_by_name_or_ticker", return_value=[])

    # 2. Mock external service to find something
    mock_details = {
        "name": "Alphabet Inc.",
        "asset_type": "STOCK",
        "currency": "USD",
        "exchange": "NASDAQ",
        "isin": "US02079K3059",
    }
    mocker.patch(
        "app.services.financial_data_service.financial_data_service.get_asset_details",
        return_value=mock_details,
    )

    # 3. Mock the create function to verify it's called
    mock_asset = Asset(id=99, ticker_symbol="GOOGL", **mock_details)
    mock_create = mocker.patch("app.crud.asset.create", return_value=mock_asset)

    # 4. Call the endpoint
    response = client.get(
        f"{settings.API_V1_STR}/assets/lookup/?query=GOOGL",
        headers=auth_headers,
    )

    # 5. Assertions
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["ticker_symbol"] == "GOOGL"
    assert data[0]["name"] == "Alphabet Inc."
    assert data[0]["id"] == 99

    # Verify that create was called with the correct data
    mock_create.assert_called_once()
    call_args = mock_create.call_args[1]['obj_in']
    assert call_args.ticker_symbol == "GOOGL"
    assert call_args.name == "Alphabet Inc."
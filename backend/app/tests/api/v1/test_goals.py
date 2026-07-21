import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.utils.asset import create_test_asset
from app.tests.utils.goal import create_random_goal
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_create_goal(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal_data = {
        "name": "Buy a car",
        "target_amount": 25000.00,
        "target_date": "2025-12-31",
    }
    response = client.post(
        "/api/v1/goals/",
        headers=headers,
        json=goal_data,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == goal_data["name"]
    assert data["target_amount"] == goal_data["target_amount"]
    assert data["target_date"] == goal_data["target_date"]
    assert data["user_id"] == str(user.id)


def test_read_goals(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    create_random_goal(db, user_id=user.id)
    create_random_goal(db, user_id=user.id)

    response = client.get("/api/v1/goals/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_read_goal_by_id(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)

    response = client.get(f"/api/v1/goals/{goal.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == goal.name
    assert data["id"] == str(goal.id)


def test_read_goal_not_found(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    non_existent_id = uuid.uuid4()
    response = client.get(f"/api/v1/goals/{non_existent_id}", headers=headers)
    assert response.status_code == 404


def test_read_goal_not_owned(client: TestClient, db: Session, get_auth_headers):
    user1, password = create_random_user(db)
    user2, _ = create_random_user(db)
    headers = get_auth_headers(user1.email, password)
    goal_for_user2 = create_random_goal(db, user_id=user2.id)

    url = f"/api/v1/goals/{goal_for_user2.id}"
    response = client.get(url, headers=headers)
    assert response.status_code == 403


def test_update_goal(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)
    new_name = "Updated Goal Name"
    new_target_amount = 30000.00
    new_target_date = "2026-12-31"

    response = client.put(
        f"/api/v1/goals/{goal.id}",
        headers=headers,
        json={
            "name": new_name,
            "target_amount": new_target_amount,
            "target_date": new_target_date,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_name
    assert data["target_amount"] == new_target_amount
    assert data["target_date"] == new_target_date
    assert data["id"] == str(goal.id)


def test_delete_goal(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)

    response = client.delete(f"/api/v1/goals/{goal.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["msg"] == "Goal deleted successfully"

    # Verify it's gone
    response = client.get(f"/api/v1/goals/{goal.id}", headers=headers)
    assert response.status_code == 404


def test_create_goal_link_with_asset(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="AAPL")
    # Need to create a transaction so the asset is "owned" by the user
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="AAPL",
        quantity=10,
        price_per_unit=100,
    )

    link_data = {"goal_id": str(goal.id), "asset_id": str(asset.id)}

    response = client.post(
        f"/api/v1/goals/{goal.id}/links", headers=headers, json=link_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["goal_id"] == str(goal.id)
    assert data["asset_id"] == str(asset.id)
    assert data["portfolio_id"] is None


def test_create_goal_link_with_portfolio(
    client: TestClient, db: Session, get_auth_headers
):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    link_data = {"goal_id": str(goal.id), "portfolio_id": str(portfolio.id)}

    response = client.post(
        f"/api/v1/goals/{goal.id}/links", headers=headers, json=link_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["goal_id"] == str(goal.id)
    assert data["portfolio_id"] == str(portfolio.id)
    assert data["asset_id"] is None


def test_delete_goal_link(client: TestClient, db: Session, get_auth_headers):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="GOOG")
    # Need to create a transaction so the asset is "owned" by the user
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="GOOG",
        quantity=10,
        price_per_unit=100,
    )
    link_data = {"goal_id": str(goal.id), "asset_id": str(asset.id)}
    response = client.post(
        f"/api/v1/goals/{goal.id}/links", headers=headers, json=link_data
    )
    link_id = response.json()["id"]

    response = client.delete(
        f"/api/v1/goals/{goal.id}/links/{link_id}", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["msg"] == "Link deleted successfully"


def test_read_goal_with_analytics(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    # Mock the financial data service to return a fixed price
    mock_price_data = {
        "AAPL": {"current_price": 150.0, "previous_close": 145.0},
    }
    mocker.patch(
        "app.services.financial_data_service.financial_data_service.get_current_prices",
        return_value=mock_price_data,
    )

    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal = create_random_goal(db, user_id=user.id, target_amount=100000)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="AAPL")
    # Create a transaction to give the asset a value
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="AAPL",
        quantity=100,
        price_per_unit=100,
    )

    # Link the asset to the goal
    link_data = {"goal_id": str(goal.id), "asset_id": str(asset.id)}
    client.post(f"/api/v1/goals/{goal.id}/links", headers=headers, json=link_data)

    response = client.get(f"/api/v1/goals/{goal.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(goal.id)
    assert data["target_amount"] == 100000
    assert data["current_amount"] == 15000  # 100 shares * $150
    assert data["progress"] == 15.0


def test_goal_sip_calculation_standard(
    client: TestClient, db: Session, get_auth_headers
):
    from datetime import date, timedelta

    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    # Target date 5 years (1825 days) into future
    target_date_str = (date.today() + timedelta(days=1825)).strftime("%Y-%m-%d")
    goal_data = {
        "name": "Retirement Fund",
        "target_amount": 1000000.0,
        "target_date": target_date_str,
        "expected_return": 12.0,
    }
    response = client.post("/api/v1/goals/", headers=headers, json=goal_data)
    assert response.status_code == 201
    goal_id = response.json()["id"]

    res = client.get(f"/api/v1/goals/{goal_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["expected_return"] == 12.0
    assert data["calculated_return_rate"] == 12.0
    # Expected SIP for 1,000,000 in 60 months @ 12% p.a. is approx 12244.45
    assert 12000.0 <= data["required_sip"] <= 12500.0


def test_goal_sip_calculation_pv_exceeds(
    client: TestClient, db: Session, get_auth_headers, mocker
):
    from datetime import date, timedelta

    mock_price_data = {"AAPL": {"current_price": 500.0, "previous_close": 500.0}}
    mocker.patch(
        "app.services.financial_data_service.financial_data_service.get_current_prices",
        return_value=mock_price_data,
    )
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    target_date_str = (date.today() + timedelta(days=1095)).strftime("%Y-%m-%d")
    resp = client.post(
        "/api/v1/goals/",
        headers=headers,
        json={
            "name": "Big Goal",
            "target_amount": 500000.0,
            "target_date": target_date_str,
            "expected_return": 10.0,
        },
    )
    goal_id = resp.json()["id"]
    portfolio = create_test_portfolio(db, user_id=user.id, name="Big Portfolio")
    asset = create_test_asset(db, ticker_symbol="AAPL")
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="AAPL",
        quantity=1000,
        price_per_unit=500,
    )
    client.post(
        f"/api/v1/goals/{goal_id}/links",
        headers=headers,
        json={"goal_id": str(goal_id), "asset_id": str(asset.id)},
    )

    res = client.get(f"/api/v1/goals/{goal_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["current_amount"] == 500000
    assert data["required_sip"] == 0.0


def test_goal_sip_calculation_zero_rate(
    client: TestClient, db: Session, get_auth_headers
):
    from datetime import date, timedelta

    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    target_date_str = (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
    goal_data = {
        "name": "Zero Return Goal",
        "target_amount": 120000.0,
        "target_date": target_date_str,
        "expected_return": 0.0,
    }
    response = client.post("/api/v1/goals/", headers=headers, json=goal_data)
    assert response.status_code == 201
    goal_id = response.json()["id"]

    res = client.get(f"/api/v1/goals/{goal_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    # 120,000 over ~12 months with 0% return rate -> ~10,000 / month
    assert 9900.0 <= data["required_sip"] <= 10100.0


def test_goal_sip_calculation_past_date(
    client: TestClient, db: Session, get_auth_headers
):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)
    goal_data = {
        "name": "Past Goal",
        "target_amount": 50000.0,
        "target_date": "2020-01-01",
        "expected_return": 10.0,
    }
    response = client.post("/api/v1/goals/", headers=headers, json=goal_data)
    assert response.status_code == 201
    goal_id = response.json()["id"]

    res = client.get(f"/api/v1/goals/{goal_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["required_sip"] == 0.0


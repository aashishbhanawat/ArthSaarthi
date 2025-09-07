import uuid
from datetime import date, timedelta
from typing import Callable, Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.recurring_deposit import RecurringDeposit
from app.schemas.recurring_deposit import RecurringDepositCreate, RecurringDepositUpdate
from app.tests.utils.user import create_random_user
from app.tests.utils.portfolio import create_test_portfolio

def create_random_rd(db: Session, portfolio_id: uuid.UUID, user_id: uuid.UUID) -> RecurringDeposit:
    rd_in = RecurringDepositCreate(
        name="Test RD",
        monthly_installment=1000,
        interest_rate=6.5,
        start_date=date.today() - timedelta(days=30),
        tenure_months=12,
    )
    return crud.recurring_deposit.create_with_portfolio(
        db=db, obj_in=rd_in, portfolio_id=portfolio_id, user_id=user_id
    )

def test_create_recurring_deposit(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    auth_headers = get_auth_headers(user.email, password)

    rd_data = {
        "name": "Test RD",
        "monthly_installment": 1000,
        "interest_rate": 6.5,
        "start_date": "2024-01-01",
        "tenure_months": 12,
    }

    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/recurring-deposits/",
        headers=auth_headers,
        json=rd_data,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == rd_data["name"]
    assert float(data["monthly_installment"]) == float(rd_data["monthly_installment"])
    assert "id" in data

def test_read_recurring_deposit(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    auth_headers = get_auth_headers(user.email, password)
    rd = create_random_rd(db, portfolio_id=portfolio.id, user_id=user.id)

    response = client.get(
        f"{settings.API_V1_STR}/recurring-deposits/{rd.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == rd.name
    assert data["id"] == str(rd.id)

def test_update_recurring_deposit(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    auth_headers = get_auth_headers(user.email, password)
    rd = create_random_rd(db, portfolio_id=portfolio.id, user_id=user.id)

    update_data = {"name": "Updated RD Name", "monthly_installment": 1500, "interest_rate": 7.0, "start_date": "2024-02-01", "tenure_months": 18}

    response = client.put(
        f"{settings.API_V1_STR}/recurring-deposits/{rd.id}",
        headers=auth_headers,
        json=update_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["id"] == str(rd.id)

def test_delete_recurring_deposit(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    auth_headers = get_auth_headers(user.email, password)
    rd = create_random_rd(db, portfolio_id=portfolio.id, user_id=user.id)

    response = client.delete(
        f"{settings.API_V1_STR}/recurring-deposits/{rd.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    response = client.get(
        f"{settings.API_V1_STR}/recurring-deposits/{rd.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404

def test_recurring_deposit_valuation():
    """
    Tests the recurring deposit valuation logic against a known-correct example.
    """
    from app.crud.crud_holding import _calculate_rd_value_at_date
    from datetime import date
    from decimal import Decimal

    # Values from CRED calculator example
    monthly_installment = Decimal("10000")
    interest_rate = Decimal("8")
    start_date = date(2023, 1, 1)
    tenure_months = 12
    maturity_date = date(2024, 1, 1)

    # The expected maturity value from the website is ₹1,25,293
    expected_maturity_value = Decimal("125293")

    calculated_maturity_value = _calculate_rd_value_at_date(
        monthly_installment=monthly_installment,
        interest_rate=interest_rate,
        start_date=start_date,
        tenure_months=tenure_months,
        calculation_date=maturity_date,
    )

    # Allow a small tolerance for rounding differences
    assert abs(calculated_maturity_value - expected_maturity_value) < 20

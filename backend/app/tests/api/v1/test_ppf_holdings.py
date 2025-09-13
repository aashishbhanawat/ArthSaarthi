from datetime import date
from decimal import Decimal
import pytest
from typing import Callable, Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.schemas import AssetType, TransactionType
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user


def seed_ppf_interest_rates(db: Session) -> None:
    """Seeds historical PPF rates for testing."""
    rates_data = [
        {"start_date": "2022-04-01", "end_date": "2023-03-31", "rate": 7.1},
        {"start_date": "2023-04-01", "end_date": "2024-03-31", "rate": 7.1},
        {"start_date": "2024-04-01", "end_date": "2025-03-31", "rate": 7.1},
        {"start_date": "2025-04-01", "end_date": "2026-03-31", "rate": 7.1},
    ]
    for rate_info in rates_data:
        crud.historical_interest_rate.create(
            db,
            obj_in=schemas.HistoricalInterestRateCreate(
                scheme_name="PPF",
                start_date=date.fromisoformat(rate_info["start_date"]),
                end_date=date.fromisoformat(rate_info["end_date"]),
                rate=rate_info["rate"],
            ),
        )


def test_ppf_interest_calculation(
    client: TestClient, db: Session, get_auth_headers: Callable[[str, str], Dict[str, str]], mocker
) -> None:
    """
    Test PPF interest calculation over a completed financial year.
    """
    user, password = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="PPF Test Portfolio")
    headers = get_auth_headers(user.email, password)
    seed_ppf_interest_rates(db)

    # Mock date.today() to have a predictable end date for calculation
    # We can't patch 'today' on the built-in date object directly.
    # Instead, we replace the 'date' class in the module where it's used.
    class MockDate(date):
        @classmethod
        def today(cls):
            return date(2025, 9, 13)
    mocker.patch("app.crud.crud_ppf.date", MockDate)

    # 1. Create PPF Account with an initial contribution
    ppf_creation_data = {
        "institution_name": "Test PPF Bank",
        "account_number": "123456",
        "opening_date": "2022-05-01",
        "amount": 10000,
        "contribution_date": "2022-05-10", # Before 5th of month doesn't apply here
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/ppf-accounts",
        headers=headers,
        json=ppf_creation_data,
    )
    assert response.status_code == 200
    ppf_asset_id = response.json()["asset"]["id"]

    # 2. Add another contribution in the same FY
    contribution_data = {
        "asset_id": ppf_asset_id,
        "transaction_type": "CONTRIBUTION",
        "quantity": 1,
        "price_per_unit": 5000,
        "transaction_date": "2022-12-01",
        "asset_type": "PPF",
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/transactions",
        headers=headers,
        json=contribution_data,
    )
    assert response.status_code == 201

    # 3. Get holdings after the FY has completed
    # The holdings endpoint will trigger the interest calculation.
    response = client.get(f"{settings.API_V1_STR}/portfolios/{portfolio.id}/holdings", headers=headers)
    assert response.status_code == 200
    holdings = response.json()["holdings"]
    ppf_holding = next((h for h in holdings if h["asset_type"] == "PPF"), None)

    # Verification
    # Interest is calculated for all *completed* financial years up to today's date (mocked to 2025-09-13)
    # FY 2022-23 Interest: 710.00
    # FY 2023-24 Interest: 15710.00 * 7.1% = 1115.41
    # FY 2024-25 Interest: 16825.41 * 7.1% = 1194.60
    # Total Credited Interest (Realized PNL) = 710.00 + 1115.41 + 1194.60 = 3020.01
    expected_realized_pnl = Decimal("3020.01")
    total_investment = Decimal("15000.00")

    # On-the-fly interest for current FY (Apr-Aug 2025, 5 months)
    # Balance at start of FY = 15000 + 3020.01 = 18020.01
    # Interest = 18020.01 * (7.1/100) * (5/12) = 533.09
    expected_unrealized_pnl = Decimal("533.09")
    expected_current_value = total_investment + expected_realized_pnl + expected_unrealized_pnl

    assert ppf_holding is not None
    print("\n--- PPF Holding Verification ---")
    print(f"Expected Total Investment: {total_investment}")
    print(f"Actual Total Investment:   {ppf_holding['total_invested_amount']}")
    print(f"Expected Realized PNL (Credited Interest): {expected_realized_pnl}")
    print(f"Actual Realized PNL:   {ppf_holding['realized_pnl']}")
    print(f"Expected Unrealized PNL (On-the-fly Interest): {expected_unrealized_pnl}")
    print(f"Actual Unrealized PNL:   {ppf_holding['unrealized_pnl']}")
    print(f"Expected Current Value (incl. on-the-fly interest): {expected_current_value.quantize(Decimal('0.01'))}")
    print(f"Actual Current Value:    {ppf_holding['current_value']}")
    print("-----------------------------\n")

    assert Decimal(ppf_holding["total_invested_amount"]).quantize(Decimal("0.01")) == total_investment
    assert Decimal(ppf_holding["realized_pnl"]).quantize(Decimal("0.01")) == expected_realized_pnl
    assert Decimal(ppf_holding["unrealized_pnl"]).quantize(Decimal("0.01")) == expected_unrealized_pnl
    assert Decimal(ppf_holding["current_value"]).quantize(Decimal("0.01")) == expected_current_value.quantize(Decimal('0.01'))

    # 4. Verify that the INTEREST_CREDIT transaction was created
    transactions = crud.transaction.get_multi_by_asset(db, asset_id=ppf_asset_id)
    interest_txn = next((t for t in transactions if t.transaction_type == TransactionType.INTEREST_CREDIT and t.transaction_date.date() == date(2023, 3, 31)), None)
    assert interest_txn is not None
    assert interest_txn.price_per_unit.quantize(Decimal("0.01")) == Decimal("710.00")


def test_ppf_smart_recalculation(
    client: TestClient, db: Session, get_auth_headers: Callable[[str, str], Dict[str, str]]
) -> None:
    """
    Test that modifying a contribution triggers interest recalculation.
    """
    user, password = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="PPF Recalc Portfolio")
    headers = get_auth_headers(user.email, password)
    seed_ppf_interest_rates(db)

    # 1. Create PPF Account with an initial contribution
    ppf_creation_data = {
        "institution_name": "Test PPF Bank Recalc",
        "account_number": "987654",
        "opening_date": "2022-05-01",
        "amount": 10000,
        "contribution_date": "2022-06-01",
    }
    response = client.post(
        f"{settings.API_V1_STR}/portfolios/{portfolio.id}/ppf-accounts",
        headers=headers,
        json=ppf_creation_data,
    )
    assert response.status_code == 200
    ppf_asset = crud.asset.get(db, id=response.json()["asset"]["id"])
    contribution_id = response.json()["id"]

    # 2. Trigger initial interest calculation
    client.get(f"{settings.API_V1_STR}/portfolios/{portfolio.id}/holdings", headers=headers)
    
    # Verify interest transaction exists
    transactions = crud.transaction.get_multi_by_asset(db, asset_id=ppf_asset.id)
    assert any(t.transaction_type == TransactionType.INTEREST_CREDIT for t in transactions)

    # 3. Delete the contribution
    # This should trigger the smart recalculation logic and delete the interest credit.
    response = client.delete(f"{settings.API_V1_STR}/portfolios/{portfolio.id}/transactions/{contribution_id}", headers=headers)
    assert response.status_code == 200

    # 4. Verify the interest transaction was deleted
    db.expire_all() # Ensure we get fresh data from the DB
    transactions = crud.transaction.get_multi_by_asset(db, asset_id=ppf_asset.id)
    assert not any(t.transaction_type == TransactionType.INTEREST_CREDIT for t in transactions)
import csv
from datetime import datetime
from io import StringIO
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.schemas.transaction import TransactionCreate
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_get_dividend_report_empty(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    user_headers = get_auth_headers(user.email, password)

    response = client.get(
        f"{settings.API_V1_STR}/dividends/?fy=2025-26", headers=user_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fy_year"] == "2025-26"
    assert data["entries"] == []
    assert data["total_amount_inr"] == "0"


def test_get_dividend_report_with_data(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    user_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Div Test Portfolio")

    asset1 = create_test_asset(db, ticker_symbol="DIV_ASSET1", currency="INR")

    # Create dividend inside FY 2025-26
    tx1_date = datetime(2025, 5, 15)

    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=asset1.id,
            transaction_type="DIVIDEND",
            quantity=10,
            price_per_unit=10, # Total dividend = 100
            transaction_date=tx1_date,
            fees=0,
        ),
        portfolio_id=portfolio.id,
    )
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/dividends/?fy=2025-26&portfolio_id={portfolio.id}",
        headers=user_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert data["fy_year"] == "2025-26"
    assert len(data["entries"]) == 1
    assert float(data["total_amount_inr"]) == 100.0

    entry = data["entries"][0]
    assert entry["asset_ticker"] == "DIV_ASSET1"
    assert float(entry["amount_native"]) == 100.0


def test_export_dividend_report_csv_with_data(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    user_headers = get_auth_headers(user.email, password)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Div Test Portfolio")

    asset1 = create_test_asset(db, ticker_symbol="DIV_ASSET2", currency="USD")

    # Create foreign dividend inside FY 2025-26
    tx1_date = datetime(2025, 6, 20)

    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=asset1.id,
            transaction_type="DIVIDEND",
            quantity=1,
            price_per_unit=50, # 50 USD
            transaction_date=tx1_date,
            fees=0,
        ),
        portfolio_id=portfolio.id,
    )
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/dividends/export?fy=2025-26&portfolio_id={portfolio.id}",
        headers=user_headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert (
        "attachment; filename=dividend_report_2025_26.csv"
        in response.headers["content-disposition"]
    )

    csv_file = StringIO(response.text)
    reader = csv.reader(csv_file)
    rows = list(reader)

    # Disclaimer, Empty, Summary Header, 5 Summary Rows, Empty, Headers, Data row
    assert len(rows) == 11

    # Extract the dynamic rate instead of hardcoding, as
    # yfinance could return diff values
    amount_native = float(rows[10][4])
    rate_str = rows[10][7]
    rate = float(rate_str) if rate_str != "N/A" else 1.0
    expected_inr = amount_native * rate

    # Verify summary section
    assert rows[2][0] == "Advance Tax Bucket"
    assert rows[3][0] == "Upto 15/6"
    assert rows[4][0] == "16/6 - 15/9"
    # Our USD dividend was on June 20, fits in 16/6 - 15/9 bucket
    assert float(rows[4][1]) == expected_inr

    # Verify detailed section
    assert rows[9][0] == "Asset Name"
    assert rows[10][1] == "DIV_ASSET2"
    assert amount_native == 50.0 # Amount native
    assert rows[10][5] == "USD"  # Currency
    assert float(rows[10][8]) == expected_inr # Amount INR
    assert rows[10][9] == "16/6 - 15/9" # Period

from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.asset import AssetCreate
from app.schemas.historical_interest_rate import HistoricalInterestRateCreate
from app.schemas.transaction import TransactionCreate
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user, get_access_token


@pytest.fixture(scope="function")
def db_with_ppf_rates(db: Session) -> Session:
    rates = [
        HistoricalInterestRateCreate(
            scheme_name="PPF",
            start_date=date(2021, 4, 1),
            end_date=date(2022, 3, 31),
            rate=Decimal("7.1"),
        ),
        HistoricalInterestRateCreate(
            scheme_name="PPF",
            start_date=date(2022, 4, 1),
            end_date=date(2023, 3, 31),
            rate=Decimal("7.1"),
        ),
        HistoricalInterestRateCreate(
            scheme_name="PPF",
            start_date=date(2023, 4, 1),
            end_date=date(2024, 3, 31),
            rate=Decimal("7.1"),
        ),
    ]
    for rate in rates:
        existing_rate = crud.historical_interest_rate.get_by_scheme_and_start_date(
            db, scheme_name=rate.scheme_name, start_date=rate.start_date
        )
        if not existing_rate:
            crud.historical_interest_rate.create(db, obj_in=rate)
    return db


def test_ppf_interest_calculation_for_completed_fy(
    db_with_ppf_rates: Session,
) -> None:
    db = db_with_ppf_rates
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="PPF Test")

    ppf_asset_in = AssetCreate(
        name="My PPF Account",
        ticker_symbol="PPF-TEST-CALC-4",
        asset_type="PPF",
        currency="INR",
        opening_date=date(2021, 5, 1),
    )
    ppf_asset = crud.asset.create(db, obj_in=ppf_asset_in)

    tx1 = TransactionCreate(
        asset_id=ppf_asset.id,
        transaction_type="CONTRIBUTION",
        quantity=Decimal("10000"),
        price_per_unit=1,
        transaction_date=datetime(2021, 4, 4),
    )
    crud.transaction.create_with_portfolio(db, portfolio_id=portfolio.id, obj_in=tx1)
    tx2 = TransactionCreate(
        asset_id=ppf_asset.id,
        transaction_type="CONTRIBUTION",
        quantity=Decimal("20000"),
        price_per_unit=1,
        transaction_date=datetime(2021, 5, 6),
    )
    crud.transaction.create_with_portfolio(db, portfolio_id=portfolio.id, obj_in=tx2)
    db.commit()

    crud.holding.get_portfolio_holdings_and_summary(db, portfolio_id=portfolio.id)

    interest_txs = db.query(models.Transaction).filter_by(
        asset_id=ppf_asset.id, transaction_type="INTEREST_CREDIT"
    ).all()

    assert len(interest_txs) >= 1
    interest_tx_fy21_22 = next(
        (tx for tx in interest_txs if tx.transaction_date.date() == date(2022, 3, 31)),
        None,
    )
    assert interest_tx_fy21_22 is not None
    expected_interest = Decimal("1893.33")
    assert interest_tx_fy21_22.quantity == pytest.approx(expected_interest, abs=0.01)


def test_ppf_smart_recalculation_on_delete(
    db_with_ppf_rates: Session, client: TestClient
) -> None:
    db = db_with_ppf_rates
    user, password = create_random_user(db)
    token = get_access_token(client, user.email, password)
    user_token_headers = {"Authorization": f"Bearer {token}"}
    portfolio = create_test_portfolio(db, user_id=user.id, name="PPF Recalc Test")

    ppf_asset_in = AssetCreate(
        name="Recalc PPF",
        ticker_symbol="PPF-RECALC-DEL-4",
        asset_type="PPF",
        currency="INR",
        opening_date=date(2021, 4, 1),
    )
    ppf_asset = crud.asset.create(db, obj_in=ppf_asset_in)

    tx_to_delete_in = TransactionCreate(
        asset_id=ppf_asset.id,
        transaction_type="CONTRIBUTION",
        quantity=Decimal("50000"),
        price_per_unit=1,
        transaction_date=datetime(2021, 6, 1),
    )
    tx_to_delete = crud.transaction.create_with_portfolio(
        db, portfolio_id=portfolio.id, obj_in=tx_to_delete_in
    )
    db.commit()

    crud.holding.get_portfolio_holdings_and_summary(db, portfolio_id=portfolio.id)

    interest_txs_before = db.query(models.Transaction).filter_by(
        asset_id=ppf_asset.id, transaction_type="INTEREST_CREDIT"
    ).count()
    assert interest_txs_before > 0

    response = client.delete(
        f"/api/v1/portfolios/{portfolio.id}/transactions/{tx_to_delete.id}",
        headers=user_token_headers,
    )
    assert response.status_code == 200, response.text

    interest_txs_after = db.query(models.Transaction).filter_by(
        asset_id=ppf_asset.id, transaction_type="INTEREST_CREDIT"
    ).count()
    assert interest_txs_after == 0

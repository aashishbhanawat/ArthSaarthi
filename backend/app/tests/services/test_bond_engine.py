import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.models.bond import Bond
from app.schemas.asset import AssetType
from app.schemas.enums import PaymentFrequency, TransactionType
from app.services.corporate_actions.bond_engine import (
    calculate_coupon_amount,
    get_bond_holding_quantity,
    get_candidate_coupon_dates,
    get_frequency_divisor,
    is_coupon_due,
    process_bond_corporate_actions,
)
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_frequency_divisor():
    assert get_frequency_divisor(PaymentFrequency.ANNUALLY) == 1
    assert get_frequency_divisor(PaymentFrequency.SEMI_ANNUALLY) == 2
    assert get_frequency_divisor(PaymentFrequency.QUARTERLY) == 4
    assert get_frequency_divisor(PaymentFrequency.MONTHLY) == 12
    assert get_frequency_divisor(PaymentFrequency.ON_MATURITY) == 1
    assert get_frequency_divisor(None) == 1


def test_is_coupon_due_annually():
    bond = Bond(
        id=uuid.uuid4(),
        asset_id=uuid.uuid4(),
        bond_type="CORPORATE",
        coupon_rate=Decimal("8.5"),
        maturity_date=date(2030, 6, 15),
        payment_frequency=PaymentFrequency.ANNUALLY,
        first_payment_date=date(2025, 6, 15),
    )
    # Due on exact anniversary
    assert is_coupon_due(bond, date(2026, 6, 15)) is True
    # Not due on other dates/months
    assert is_coupon_due(bond, date(2026, 6, 14)) is False
    assert is_coupon_due(bond, date(2026, 7, 15)) is False
    # Not due before first_payment_date
    assert is_coupon_due(bond, date(2024, 6, 15)) is False
    # Not due after maturity_date
    assert is_coupon_due(bond, date(2031, 6, 15)) is False


def test_is_coupon_due_semi_annually():
    bond = Bond(
        id=uuid.uuid4(),
        asset_id=uuid.uuid4(),
        bond_type="CORPORATE",
        coupon_rate=Decimal("7.0"),
        maturity_date=date(2030, 8, 31),
        payment_frequency=PaymentFrequency.SEMI_ANNUALLY,
        first_payment_date=date(2025, 8, 31),
    )
    # Aug 31
    assert is_coupon_due(bond, date(2026, 8, 31)) is True
    # Feb (6 months later) in non-leap year (2026 has 28 days)
    assert is_coupon_due(bond, date(2026, 2, 28)) is True
    assert is_coupon_due(bond, date(2026, 2, 27)) is False
    # Feb in leap year (2028 has 29 days)
    assert is_coupon_due(bond, date(2028, 2, 29)) is True


def test_is_coupon_due_on_maturity():
    bond = Bond(
        id=uuid.uuid4(),
        asset_id=uuid.uuid4(),
        bond_type="CORPORATE",
        coupon_rate=Decimal("9.0"),
        maturity_date=date(2027, 12, 1),
        payment_frequency=PaymentFrequency.ON_MATURITY,
    )
    assert is_coupon_due(bond, date(2026, 12, 1)) is False
    assert is_coupon_due(bond, date(2027, 12, 1)) is True


def test_calculate_coupon_amount():
    bond = Bond(
        id=uuid.uuid4(),
        asset_id=uuid.uuid4(),
        bond_type="CORPORATE",
        face_value=Decimal("1000.00"),
        coupon_rate=Decimal("8.0"),  # 8% per year = 80 per unit
        maturity_date=date(2030, 1, 1),
        payment_frequency=PaymentFrequency.SEMI_ANNUALLY,  # 40 per unit
    )
    # 10 units * 40 = 400.00
    amount = calculate_coupon_amount(bond, Decimal("10"))
    assert amount == Decimal("400.00")

    # Quarterly with 5 units: 80 / 4 * 5 = 100.00
    bond.payment_frequency = PaymentFrequency.QUARTERLY
    assert calculate_coupon_amount(bond, Decimal("5")) == Decimal("100.00")


def test_process_bond_corporate_actions_end_to_end(db: Session):
    # Setup test user, portfolio, bond asset
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Bonds Portfolio")

    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            name="7.5% Sovereign Bond 2026",
            ticker_symbol=f"SGB-{uuid.uuid4().hex[:6]}",
            asset_type=AssetType.BOND,
            currency="INR",
        ),
    )

    today = date(2026, 11, 8)
    bond = Bond(
        id=uuid.uuid4(),
        asset_id=asset.id,
        bond_type="GOVERNMENT",
        face_value=Decimal("1000.00"),
        coupon_rate=Decimal("7.5"),
        maturity_date=date(2030, 11, 8),
        payment_frequency=PaymentFrequency.ANNUALLY,
        first_payment_date=date(2026, 11, 8),
        isin="IN0020200001",
    )
    db.add(bond)
    db.commit()

    # Buy 20 units on 2026-11-01
    buy_tx = schemas.TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("20"),
        price_per_unit=Decimal("1000.00"),
        fees=Decimal("0.0"),
        transaction_date=datetime(2026, 11, 1, 0, 0),
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=buy_tx, portfolio_id=portfolio.id
    )
    db.commit()

    qty = get_bond_holding_quantity(db, str(portfolio.id), str(asset.id), today)
    assert qty == Decimal("20")

    # Run processing on today (2026-11-08) -> Annual coupon matches!
    events = process_bond_corporate_actions(db, check_date=today)
    assert len(events) == 1
    event = events[0]
    assert event.event_type == "BOND_COUPON"
    # Coupon: 20 units * (1000 * 7.5% / 1) = 1,500.00
    assert event.amount == Decimal("1500.00")
    assert event.status == "NEW"

    # Verify transaction created
    coupon_tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.portfolio_id == portfolio.id,
            models.Transaction.transaction_type == "COUPON",
        )
        .first()
    )
    assert coupon_tx is not None
    assert coupon_tx.is_automated is True
    assert coupon_tx.quantity == Decimal("1500.00")

    # IDEMPOTENCY: Run again on same day -> must NOT create duplicate!
    duplicate_events = process_bond_corporate_actions(db, check_date=today)
    assert len(duplicate_events) == 0

    total_coupons = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.portfolio_id == portfolio.id,
            models.Transaction.transaction_type == "COUPON",
        )
        .count()
    )
    assert total_coupons == 1


def test_get_candidate_coupon_dates_annually():
    bond = Bond(
        id=uuid.uuid4(),
        asset_id=uuid.uuid4(),
        bond_type="GOVERNMENT",
        coupon_rate=Decimal("7.5"),
        maturity_date=date(2030, 11, 14),
        payment_frequency=PaymentFrequency.ANNUALLY,
        first_payment_date=date(2025, 11, 14),
    )
    # Range covering 2025 to 2027
    dates = get_candidate_coupon_dates(bond, date(2025, 1, 1), date(2027, 12, 31))
    assert dates == [date(2025, 11, 14), date(2026, 11, 14), date(2027, 11, 14)]


def test_get_candidate_coupon_dates_month_end_leap_year():
    bond = Bond(
        id=uuid.uuid4(),
        asset_id=uuid.uuid4(),
        bond_type="CORPORATE",
        coupon_rate=Decimal("8.0"),
        maturity_date=date(2030, 8, 31),
        payment_frequency=PaymentFrequency.SEMI_ANNUALLY,
        first_payment_date=date(2026, 8, 31),
    )
    # Range from 2027 to 2028 (2028 is a leap year with Feb 29)
    dates = get_candidate_coupon_dates(bond, date(2027, 1, 1), date(2028, 12, 31))
    # 2027: Feb 28, Aug 31
    # 2028: Feb 29 (leap!), Aug 31
    assert dates == [
        date(2027, 2, 28),
        date(2027, 8, 31),
        date(2028, 2, 29),
        date(2028, 8, 31),
    ]


def test_process_bond_corporate_actions_catchup_after_downtime(db: Session):
    """
    Validates the downtime catch-up / backfill scenario:
    - User closed app on Nov 12th.
    - Coupon was due on Nov 14th.
    - User reopened app / system on Nov 16th.
    - The engine must catch up and automatically credit the Nov 14th coupon.
    """
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Catchup Portfolio")

    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            name="7.18% GS 2033",
            ticker_symbol=f"GS33-{uuid.uuid4().hex[:6]}",
            asset_type=AssetType.BOND,
            currency="INR",
        ),
    )

    bond = Bond(
        id=uuid.uuid4(),
        asset_id=asset.id,
        bond_type="GOVERNMENT",
        face_value=Decimal("1000.00"),
        coupon_rate=Decimal("7.18"),
        maturity_date=date(2033, 11, 14),
        payment_frequency=PaymentFrequency.ANNUALLY,
        first_payment_date=date(2024, 11, 14),
        isin="IN0020230085",
    )
    db.add(bond)
    db.commit()

    # User bought bond on Nov 1, 2026
    buy_tx = schemas.TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("10"),
        price_per_unit=Decimal("1000.00"),
        fees=Decimal("0.0"),
        transaction_date=datetime(2026, 11, 1, 10, 0),
    )
    crud.transaction.create_with_portfolio(db, obj_in=buy_tx, portfolio_id=portfolio.id)
    db.commit()

    # App is reopened on Nov 16th (two days after scheduled Nov 14th coupon!)
    reopened_date = date(2026, 11, 16)
    events = process_bond_corporate_actions(db, check_date=reopened_date)

    # Must generate 1 backfilled coupon event for Nov 14th
    assert len(events) == 1
    event = events[0]
    assert event.event_type == "BOND_COUPON"
    assert event.event_date == date(2026, 11, 14)
    # Coupon: 10 units * (1000 * 7.18%) = 71.80 * 10 = 718.00
    assert event.amount == Decimal("718.00")

    # Transaction date should be Nov 14th (the actual coupon date)
    tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.portfolio_id == portfolio.id,
            models.Transaction.transaction_type == "COUPON",
        )
        .first()
    )
    assert tx is not None
    assert tx.transaction_date.date() == date(2026, 11, 14)
    assert tx.is_automated is True

    # Idempotent: running again on Nov 16th must NOT duplicate
    duplicate_events = process_bond_corporate_actions(db, check_date=reopened_date)
    assert len(duplicate_events) == 0


def test_process_bond_corporate_actions_maturity_catchup_after_downtime(db: Session):
    """
    Validates maturity redemption catch-up when app was closed during maturity date.
    - Bond matures on Nov 14th.
    - User opens app on Nov 16th.
    - Redemptions must be processed with transaction_date = Nov 14th.
    """
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Maturity Catchup Port")

    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            name="Maturing Bond 2026",
            ticker_symbol=f"MAT-{uuid.uuid4().hex[:6]}",
            asset_type=AssetType.BOND,
            currency="INR",
        ),
    )

    maturity_date = date(2026, 11, 14)
    bond = Bond(
        id=uuid.uuid4(),
        asset_id=asset.id,
        bond_type="CORPORATE",
        face_value=Decimal("1000.00"),
        coupon_rate=Decimal("10.0"),
        maturity_date=maturity_date,
        payment_frequency=PaymentFrequency.ON_MATURITY,
        isin="INE000000099",
    )
    db.add(bond)
    db.commit()

    # Buy 5 units on 2026-01-01
    buy_tx = schemas.TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("5"),
        price_per_unit=Decimal("1000.00"),
        fees=Decimal("0.0"),
        transaction_date=datetime(2026, 1, 1, 9, 30),
    )
    crud.transaction.create_with_portfolio(db, obj_in=buy_tx, portfolio_id=portfolio.id)
    db.commit()

    # App was closed on Nov 14th, reopened on Nov 16th
    reopened_date = date(2026, 11, 16)
    events = process_bond_corporate_actions(db, check_date=reopened_date)

    # ON_MATURITY bond pays coupon + maturity redemption
    assert len(events) == 2
    types = {e.event_type for e in events}
    assert "BOND_COUPON" in types
    assert "BOND_MATURITY" in types

    maturity_event = next(e for e in events if e.event_type == "BOND_MATURITY")
    assert maturity_event.amount == Decimal("5000.00")  # 5 units * 1000 face value
    assert maturity_event.event_date == maturity_date

    coupon_event = next(e for e in events if e.event_type == "BOND_COUPON")
    assert coupon_event.amount == Decimal("500.00")  # 5 units * 1000 * 10%
    assert coupon_event.event_date == maturity_date

    # Verify SELL transaction created with maturity date
    sell_tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.portfolio_id == portfolio.id,
            models.Transaction.transaction_type == "SELL",
        )
        .first()
    )
    assert sell_tx is not None
    assert sell_tx.transaction_date.date() == maturity_date
    assert sell_tx.is_automated is True

import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.schemas.asset import AssetType
from app.schemas.enums import TransactionType
from app.schemas.stock_corporate_action import RawStockCorporateAction
from app.services.corporate_actions.parser import (
    parse_action_details,
    parse_bse_corporate_action,
    parse_nse_corporate_action,
)
from app.services.corporate_actions.stock_engine import (
    process_stock_corporate_actions,
)
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_parse_action_details():
    # Dividend tests
    action, amt, num, den = parse_action_details("Interim Dividend - Rs 10 Per Share")
    assert action == "DIVIDEND"
    assert amt == Decimal("10")

    action, amt, num, den = parse_action_details("Special Dividend - Rs. 28.50/- Per Share")
    assert action == "DIVIDEND"
    assert amt == Decimal("28.50")

    action, amt, num, den = parse_action_details("Dividend - Re 1 Per Share")
    assert action == "DIVIDEND"
    assert amt == Decimal("1")

    # Split tests
    action, amt, num, den = parse_action_details("Face Value Split From Rs 10/- To Rs 2/-")
    assert action == "SPLIT"
    assert num == Decimal("5")  # 10 / 2 = 5:1
    assert den == Decimal("1")

    action, amt, num, den = parse_action_details("Stock Split 2:1")
    assert action == "SPLIT"
    assert num == Decimal("2")
    assert den == Decimal("1")

    # Bonus tests
    action, amt, num, den = parse_action_details("Bonus 1:1")
    assert action == "BONUS"
    assert num == Decimal("1")
    assert den == Decimal("1")

    action, amt, num, den = parse_action_details("Bonus Issue 1:2")
    assert action == "BONUS"
    assert num == Decimal("1")
    assert den == Decimal("2")


def test_parse_nse_corporate_action():
    item = {
        "symbol": "TCS",
        "series": "EQ",
        "subject": "Interim Dividend - Rs 10 Per Share",
        "exDate": "14-Nov-2026",
        "recDate": "15-Nov-2026",
    }
    parsed = parse_nse_corporate_action(item)
    assert parsed is not None
    assert parsed.symbol == "TCS"
    assert parsed.action_type == "DIVIDEND"
    assert parsed.ex_date == date(2026, 11, 14)
    assert parsed.dividend_amount == Decimal("10")
    assert parsed.source == "NSE"


def test_parse_bse_corporate_action():
    item = {
        "scripcode": "532540",
        "short_name": "TCS LTD",
        "Purpose": "Interim Dividend - Rs. - 6.0000",
        "Ex_date": "02 Jan 2026",
        "RD_Date": "03 Jan 2026",
    }
    parsed = parse_bse_corporate_action(item)
    assert parsed is not None
    assert parsed.symbol == "TCS"
    assert parsed.action_type == "DIVIDEND"
    assert parsed.ex_date == date(2026, 1, 2)
    assert parsed.dividend_amount == Decimal("6.0000")
    assert parsed.source == "BSE"


def test_process_stock_corporate_actions_dividend_end_to_end(db: Session):
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Equity Dividend Port")

    ticker = f"INFY_{uuid.uuid4().hex[:6]}"
    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            name="Infosys Ltd",
            ticker_symbol=ticker,
            asset_type=AssetType.STOCK,
            currency="INR",
        ),
    )

    # Buy 100 shares on 2026-01-01
    buy_tx = schemas.TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("100"),
        price_per_unit=Decimal("1500.00"),
        fees=Decimal("0.0"),
        transaction_date=datetime(2026, 1, 1, 9, 15),
    )
    crud.transaction.create_with_portfolio(db, obj_in=buy_tx, portfolio_id=portfolio.id)
    db.commit()

    ex_date = date(2026, 11, 8)
    custom_actions = [
        RawStockCorporateAction(
            symbol=ticker,
            action_type="DIVIDEND",
            ex_date=ex_date,
            dividend_amount=Decimal("15.00"),
            source="NSE",
        )
    ]

    # Process corporate actions as of 2026-11-10
    events = process_stock_corporate_actions(
        db, check_date=date(2026, 11, 10), custom_actions=custom_actions
    )

    assert len(events) == 1
    event = events[0]
    assert event.event_type == "DIVIDEND"
    assert event.amount == Decimal("1500.00")  # 100 shares * 15
    assert event.status == "NEW"

    # Verify transaction created
    div_tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.portfolio_id == portfolio.id,
            models.Transaction.transaction_type == "DIVIDEND",
        )
        .first()
    )
    assert div_tx is not None
    assert div_tx.is_automated is True
    assert div_tx.quantity == Decimal("1500.00")

    # Idempotency check: run again on 2026-11-10 -> no duplicate
    duplicate_events = process_stock_corporate_actions(
        db, check_date=date(2026, 11, 10), custom_actions=custom_actions
    )
    assert len(duplicate_events) == 0


def test_process_stock_corporate_actions_split_end_to_end(db: Session):
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Split Port")

    ticker = f"TATAMOT_{uuid.uuid4().hex[:6]}"
    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            name="Tata Motors Ltd",
            ticker_symbol=ticker,
            asset_type=AssetType.STOCK,
            currency="INR",
        ),
    )

    # Buy 50 shares at 1000 INR on 2026-01-01
    buy_tx = schemas.TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("50"),
        price_per_unit=Decimal("1000.00"),
        fees=Decimal("0.0"),
        transaction_date=datetime(2026, 1, 1, 9, 30),
    )
    crud.transaction.create_with_portfolio(db, obj_in=buy_tx, portfolio_id=portfolio.id)
    db.commit()

    # 2:1 stock split on 2026-06-01
    ex_date = date(2026, 6, 1)
    custom_actions = [
        RawStockCorporateAction(
            symbol=ticker,
            action_type="SPLIT",
            ex_date=ex_date,
            ratio_numerator=Decimal("2"),
            ratio_denominator=Decimal("1"),
            source="NSE",
        )
    ]

    events = process_stock_corporate_actions(
        db, check_date=date(2026, 6, 5), custom_actions=custom_actions
    )
    assert len(events) == 1
    assert events[0].event_type == "SPLIT"

    # Verify SPLIT transaction exists
    split_tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.portfolio_id == portfolio.id,
            models.Transaction.transaction_type == "SPLIT",
        )
        .first()
    )
    assert split_tx is not None
    assert split_tx.is_automated is True

    # Idempotency: run again -> no duplicate
    duplicate_events = process_stock_corporate_actions(
        db, check_date=date(2026, 6, 5), custom_actions=custom_actions
    )
    assert len(duplicate_events) == 0


def test_process_stock_corporate_actions_bonus_end_to_end(db: Session):
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Bonus Port")

    ticker = f"RELIANCE_{uuid.uuid4().hex[:6]}"
    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            name="Reliance Industries",
            ticker_symbol=ticker,
            asset_type=AssetType.STOCK,
            currency="INR",
        ),
    )

    # Buy 100 shares on 2026-01-01
    buy_tx = schemas.TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("100"),
        price_per_unit=Decimal("2500.00"),
        fees=Decimal("0.0"),
        transaction_date=datetime(2026, 1, 1, 9, 30),
    )
    crud.transaction.create_with_portfolio(db, obj_in=buy_tx, portfolio_id=portfolio.id)
    db.commit()

    # 1:1 Bonus issue on 2026-10-28
    ex_date = date(2026, 10, 28)
    custom_actions = [
        RawStockCorporateAction(
            symbol=ticker,
            action_type="BONUS",
            ex_date=ex_date,
            ratio_numerator=Decimal("1"),
            ratio_denominator=Decimal("1"),
            source="NSE",
        )
    ]

    events = process_stock_corporate_actions(
        db, check_date=date(2026, 11, 1), custom_actions=custom_actions
    )
    assert len(events) == 1
    assert events[0].event_type == "BONUS"

    # Verify zero-cost bonus BUY was created (price_per_unit = 0)
    bonus_buy_tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.portfolio_id == portfolio.id,
            models.Transaction.transaction_type == "BUY",
            models.Transaction.price_per_unit == Decimal("0.0"),
        )
        .first()
    )
    assert bonus_buy_tx is not None
    assert bonus_buy_tx.quantity == Decimal("100")

    # Idempotency
    duplicate_events = process_stock_corporate_actions(
        db, check_date=date(2026, 11, 1), custom_actions=custom_actions
    )
    assert len(duplicate_events) == 0


def test_process_stock_corporate_actions_zero_holdings_skipped(db: Session):
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Zero Holdings Port")

    ticker = f"SOLD_{uuid.uuid4().hex[:6]}"
    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            name="Sold Stock",
            ticker_symbol=ticker,
            asset_type=AssetType.STOCK,
            currency="INR",
        ),
    )

    # Buy 50 on Jan 1, Sell 50 on Jan 10
    buy_tx = schemas.TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("50"),
        price_per_unit=Decimal("100.00"),
        transaction_date=datetime(2026, 1, 1, 10, 0),
    )
    crud.transaction.create_with_portfolio(db, obj_in=buy_tx, portfolio_id=portfolio.id)

    sell_tx = schemas.TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.SELL,
        quantity=Decimal("50"),
        price_per_unit=Decimal("110.00"),
        transaction_date=datetime(2026, 1, 10, 10, 0),
    )
    crud.transaction.create_with_portfolio(db, obj_in=sell_tx, portfolio_id=portfolio.id)
    db.commit()

    # Dividend on Jan 15 (after 100% was sold)
    custom_actions = [
        RawStockCorporateAction(
            symbol=ticker,
            action_type="DIVIDEND",
            ex_date=date(2026, 1, 15),
            dividend_amount=Decimal("5.00"),
        )
    ]

    events = process_stock_corporate_actions(
        db, check_date=date(2026, 1, 20), custom_actions=custom_actions
    )
    assert len(events) == 0

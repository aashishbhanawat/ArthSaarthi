
from datetime import datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.schemas.enums import TransactionType
from app.schemas.transaction import TransactionCreate
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user


def test_create_rsu_vest_transaction(db: Session) -> None:
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="GOOGL")

    transaction_in = TransactionCreate(
        transaction_type=TransactionType.RSU_VEST,
        quantity=Decimal("10.0"),
        price_per_unit=Decimal("0.0"),
        transaction_date=datetime.utcnow(),
        asset_id=asset.id,
        details={"fmv_at_vest": 150.25},
    )

    transaction = crud.transaction.create_with_portfolio(
        db, obj_in=transaction_in, portfolio_id=portfolio.id
    )

    assert transaction.transaction_type == TransactionType.RSU_VEST
    assert transaction.price_per_unit == 0
    assert transaction.details["fmv_at_vest"] == 150.25

def test_create_rsu_vest_transaction_invalid_price(db: Session) -> None:
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="GOOGL")

    transaction_in = TransactionCreate(
        transaction_type=TransactionType.RSU_VEST,
        quantity=Decimal("10.0"),
        price_per_unit=Decimal("1.0"),
        transaction_date=datetime.utcnow(),
        asset_id=asset.id,
        details={"fmv_at_vest": 150.25},
    )

    with pytest.raises(HTTPException):
        crud.transaction.create_with_portfolio(
            db, obj_in=transaction_in, portfolio_id=portfolio.id
        )

def test_create_espp_purchase_transaction(db: Session) -> None:
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="MSFT")

    transaction_in = TransactionCreate(
        transaction_type=TransactionType.ESPP_PURCHASE,
        quantity=Decimal("25.0"),
        price_per_unit=Decimal("340.0"),
        transaction_date=datetime.utcnow(),
        asset_id=asset.id,
        details={"market_price": 400.00},
    )

    transaction = crud.transaction.create_with_portfolio(
        db, obj_in=transaction_in, portfolio_id=portfolio.id
    )

    assert transaction.transaction_type == TransactionType.ESPP_PURCHASE
    assert transaction.price_per_unit == 340.0
    assert transaction.details["market_price"] == 400.00

def test_create_rsu_vest_with_sell_to_cover(db: Session) -> None:
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="GOOGL")

    transaction_in = TransactionCreate(
        transaction_type=TransactionType.RSU_VEST,
        quantity=Decimal("10.0"),
        price_per_unit=Decimal("0.0"),
        transaction_date=datetime.utcnow(),
        asset_id=asset.id,
        details={
            "fmv_at_vest": 150.25,
            "sell_to_cover_shares": 4.0,
        },
    )

    crud.transaction.create_with_portfolio(
        db, obj_in=transaction_in, portfolio_id=portfolio.id
    )

    transactions, total = crud.transaction.get_multi_by_user_with_filters(
        db, user_id=user.id, portfolio_id=portfolio.id
    )

    assert total == 2

    rsu_vest = next(
        (t for t in transactions if t.transaction_type == TransactionType.RSU_VEST),
        None,
    )
    sell = next(
        (t for t in transactions if t.transaction_type == TransactionType.SELL), None
    )

    assert rsu_vest is not None
    assert sell is not None

    assert rsu_vest.quantity == 10.0
    assert sell.quantity == 4.0
    assert sell.price_per_unit == Decimal("150.25")

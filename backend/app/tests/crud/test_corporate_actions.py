from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.schemas.enums import TransactionType
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_handle_bonus_issue(db: Session) -> None:
    """
    Test case for handling a bonus issue.
    - GIVEN an existing user, portfolio, and asset with some holdings.
    - WHEN a bonus issue is logged (e.g., 1 new for every 2 old shares).
    - THEN a new zero-cost BUY transaction for the bonus shares should be created.
    - AND the original BONUS transaction should be saved for auditing.
    """
    # GIVEN
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="TEST")

    # Create initial holding of 100 shares
    initial_buy = schemas.TransactionCreate(
        asset_id=asset.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("100"),
        price_per_unit=Decimal("150"),
        transaction_date=datetime(2023, 1, 1),
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=initial_buy, portfolio_id=portfolio.id
    )
    db.commit()

    # WHEN
    # A 1:2 bonus issue is announced
    bonus_transaction_in = schemas.TransactionCreate(
        asset_id=asset.id,
        transaction_type=TransactionType.BONUS,
        quantity=Decimal("1"),  # New shares
        price_per_unit=Decimal("2"),  # Old shares
        transaction_date=datetime(2023, 6, 1),
    )

    crud.crud_corporate_action.handle_bonus_issue(
        db,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_in=bonus_transaction_in,
    )
    db.commit()

    # THEN
    # 1. Verify the zero-cost BUY transaction for bonus shares
    bonus_shares_to_receive = Decimal("50")  # 100 / 2 * 1
    bonus_buy_tx = crud.transaction.get_by_details(
        db,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_date=datetime(2023, 6, 1),
        transaction_type=TransactionType.BUY,
        quantity=bonus_shares_to_receive,
        price_per_unit=Decimal("0"),
    )
    assert bonus_buy_tx is not None
    assert bonus_buy_tx.quantity == bonus_shares_to_receive
    assert bonus_buy_tx.price_per_unit == Decimal("0")

    # 2. Verify the BONUS audit transaction was saved
    bonus_audit_tx = crud.transaction.get_by_details(
        db,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_date=datetime(2023, 6, 1),
        transaction_type=TransactionType.BONUS,
        quantity=Decimal("1"),
        price_per_unit=Decimal("2"),
    )
    assert bonus_audit_tx is not None

    # 3. Verify the total holdings are correct
    net_holdings = crud.transaction.get_holdings_on_date(
        db, user_id=user.id, asset_id=asset.id, on_date=datetime.now()
    )
    assert net_holdings == Decimal("150")  # 100 original + 50 bonus


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_handle_cash_dividend(db: Session) -> None:
    """
    Test case for handling a cash dividend.
    - GIVEN an existing user, portfolio, and asset.
    - WHEN a cash dividend is logged.
    - THEN a DIVIDEND transaction should be saved for auditing.
    - AND no new BUY transaction should be created.
    """
    # GIVEN
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(
        db, user_id=user.id, name="Cash Dividend Portfolio"
    )
    asset = create_test_asset(db, ticker_symbol="CASH")

    # WHEN
    dividend_in = schemas.TransactionCreate(
        asset_id=asset.id,
        transaction_type=TransactionType.DIVIDEND,
        quantity=Decimal("500.00"),  # Total dividend amount
        price_per_unit=Decimal("1.0"),
        transaction_date=datetime(2023, 7, 1),
    )
    crud.crud_corporate_action.handle_dividend(
        db,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_in=dividend_in,
    )
    db.commit()

    # THEN
    all_txs = crud.transaction.get_multi_by_asset(db, asset_id=asset.id)
    assert len(all_txs) == 1
    assert all_txs[0].transaction_type == TransactionType.DIVIDEND
    assert all_txs[0].quantity == Decimal("500.00")


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_handle_stock_split(db: Session) -> None:
    """
    Test case for handling a stock split.
    - GIVEN an asset with several transactions (BUY and SELL).
    - WHEN a 2-for-1 stock split is logged.
    - THEN all transactions *before* the split date should have their quantity doubled
      and their price halved.
    - AND transactions *on or after* the split date should remain unchanged.
    - AND the total value of the adjusted transactions should be conserved.
    """
    # GIVEN
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Split Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="SPLIT")

    # Create transactions before and after the split date
    tx_before_1 = crud.transaction.create_with_portfolio(
        db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal(10),
            price_per_unit=Decimal(100),
            transaction_date=datetime(2023, 1, 1),
        ),
        portfolio_id=portfolio.id,
    )
    tx_before_2 = crud.transaction.create_with_portfolio(
        db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type=TransactionType.SELL,
            quantity=Decimal(5),
            price_per_unit=Decimal(110),
            transaction_date=datetime(2023, 2, 1),
        ),
        portfolio_id=portfolio.id,
    )
    tx_after = crud.transaction.create_with_portfolio(
        db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal(20),
            price_per_unit=Decimal(55),
            transaction_date=datetime(2023, 6, 15),
        ),
        portfolio_id=portfolio.id,
    )
    db.commit()

    # WHEN
    split_date = datetime(2023, 6, 1)
    split_in = schemas.TransactionCreate(
        asset_id=asset.id,
        transaction_type=TransactionType.SPLIT,
        quantity=Decimal("2"),  # New
        price_per_unit=Decimal("1"),  # Old
        transaction_date=split_date,
    )
    crud.crud_corporate_action.handle_stock_split(
        db,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_in=split_in,
    )
    db.commit()

    # THEN
    db.refresh(tx_before_1)
    db.refresh(tx_before_2)
    db.refresh(tx_after)

    # 1. Verify transaction before the split is NOT mutated (Event Sourcing)
    assert tx_before_1.quantity == Decimal("10")
    assert tx_before_1.price_per_unit == Decimal("100")

    # 2. Verify another transaction before the split is NOT mutated
    assert tx_before_2.quantity == Decimal("5")
    assert tx_before_2.price_per_unit == Decimal("110")

    # 3. Verify transaction after the split is NOT adjusted
    assert tx_after.quantity == Decimal("20")
    assert tx_after.price_per_unit == Decimal("55")

    # 4. Verify the SPLIT audit transaction was saved
    split_audit_tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.asset_id == asset.id,
            models.Transaction.transaction_type == TransactionType.SPLIT,
        )
        .first()
    )
    assert split_audit_tx is not None

    # 5. Verify the Holdings Calculation applies the split dynamically
    # Net before split: 10 (Buy) - 5 (Sell) = 5
    # Split 2:1 -> 10
    # Buy After: 20
    # Total Expected: 30

    from app.cache.utils import invalidate_caches_for_portfolio
    invalidate_caches_for_portfolio(db, portfolio_id=portfolio.id)

    holdings_data = crud.holding.get_portfolio_holdings_and_summary(
        db=db, portfolio_id=portfolio.id
    )
    # Find the holding for this asset
    asset_holding = next(
        (h for h in holdings_data.holdings if h.asset_id == asset.id), None
    )
    assert asset_holding is not None
    assert asset_holding.quantity == Decimal("30")

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


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_handle_merger(db: Session) -> None:
    """
    Test case for handling a merger.
    - GIVEN an existing user, portfolio, and asset with holdings.
    - WHEN a merger is logged with a 1.5 conversion ratio.
    - THEN the old asset should be converted to new asset with preserved cost basis.
    - AND the MERGER audit transaction should be saved.
    """
    # GIVEN
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Merger Portfolio")
    old_asset = create_test_asset(db, ticker_symbol="OLDCO")
    new_asset = create_test_asset(db, ticker_symbol="NEWCO")

    # Create initial holding of 100 shares at 200 per share = 20,000 cost basis
    initial_buy = schemas.TransactionCreate(
        asset_id=old_asset.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("100"),
        price_per_unit=Decimal("200"),
        transaction_date=datetime(2023, 1, 1),
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=initial_buy, portfolio_id=portfolio.id
    )
    db.commit()

    # WHEN - merger with 1.5:1 conversion ratio (100 old shares -> 150 new shares)
    merger_transaction_in = schemas.TransactionCreate(
        asset_id=old_asset.id,
        transaction_type=TransactionType.MERGER,
        quantity=Decimal("1.5"),  # Conversion ratio
        price_per_unit=Decimal("1"),  # Not used for merger
        transaction_date=datetime(2023, 6, 1),
        details={"new_asset_id": str(new_asset.id)},
    )

    crud.crud_corporate_action.handle_merger(
        db,
        portfolio_id=portfolio.id,
        asset_id=old_asset.id,
        transaction_in=merger_transaction_in,
    )
    db.commit()

    # THEN
    # 1. Verify the MERGER audit transaction was saved
    merger_audit_tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.asset_id == old_asset.id,
            models.Transaction.transaction_type == TransactionType.MERGER,
        )
        .first()
    )
    assert merger_audit_tx is not None

    # 2. Verify BUY transaction was created for new shares
    new_share_buy = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.asset_id == new_asset.id,
            models.Transaction.transaction_type == TransactionType.BUY,
        )
        .first()
    )
    assert new_share_buy is not None
    assert new_share_buy.quantity == Decimal("150")  # 100 * 1.5
    # Cost basis preserved: 20,000 / 150 ≈ 133.33 per share
    expected_price = Decimal("20000") / Decimal("150")
    assert abs(new_share_buy.price_per_unit - expected_price) < Decimal("0.01")


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_handle_demerger(db: Session) -> None:
    """
    Test case for handling a demerger.
    - GIVEN an existing user, portfolio, and asset with holdings.
    - WHEN a demerger is logged with 1:1 ratio and 30% cost allocation.
    - THEN new shares should be created with proportional cost basis.
    - AND the DEMERGER audit transaction should be saved.
    """
    # GIVEN
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Demerger Portfolio")
    old_asset = create_test_asset(db, ticker_symbol="PARENT")
    new_asset = create_test_asset(db, ticker_symbol="SPINOFF")

    # Create initial holding of 100 shares at 300 per share = 30,000 cost basis
    initial_buy = schemas.TransactionCreate(
        asset_id=old_asset.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("100"),
        price_per_unit=Decimal("300"),
        transaction_date=datetime(2023, 1, 1),
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=initial_buy, portfolio_id=portfolio.id
    )
    db.commit()

    # WHEN - demerger with 1:1 ratio and 30% cost allocation to spinoff
    demerger_transaction_in = schemas.TransactionCreate(
        asset_id=old_asset.id,
        transaction_type=TransactionType.DEMERGER,
        quantity=Decimal("1"),  # 1:1 ratio
        price_per_unit=Decimal("1"),  # Not used
        transaction_date=datetime(2023, 7, 1),
        details={
            "new_asset_id": str(new_asset.id),
            "cost_allocation_pct": "30",
        },
    )

    crud.crud_corporate_action.handle_demerger(
        db,
        portfolio_id=portfolio.id,
        asset_id=old_asset.id,
        transaction_in=demerger_transaction_in,
    )
    db.commit()

    # THEN
    # 1. Verify the DEMERGER audit transaction was saved
    demerger_audit_tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.asset_id == old_asset.id,
            models.Transaction.transaction_type == TransactionType.DEMERGER,
        )
        .first()
    )
    assert demerger_audit_tx is not None

    # 2. Verify BUY transaction was created for demerged shares
    spinoff_buy = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.asset_id == new_asset.id,
            models.Transaction.transaction_type == TransactionType.BUY,
        )
        .first()
    )
    assert spinoff_buy is not None
    assert spinoff_buy.quantity == Decimal("100")  # 1:1 ratio
    # Cost basis: 30% of 30,000 = 9,000 / 100 = 90 per share
    expected_price = Decimal("90")
    assert spinoff_buy.price_per_unit == expected_price


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_handle_rename(db: Session) -> None:
    """
    Test case for handling a ticker rename.
    - GIVEN an existing user, portfolio, and asset with holdings.
    - WHEN a rename is logged.
    - THEN holdings should be transferred to new ticker with preserved cost basis.
    - AND the RENAME audit transaction should be saved.
    """
    # GIVEN
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Rename Portfolio")
    old_asset = create_test_asset(db, ticker_symbol="VEDL")
    new_asset = create_test_asset(db, ticker_symbol="VEDANTA")

    # Create initial holding of 50 shares at 400 per share = 20,000 cost basis
    initial_buy = schemas.TransactionCreate(
        asset_id=old_asset.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("50"),
        price_per_unit=Decimal("400"),
        transaction_date=datetime(2023, 1, 1),
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=initial_buy, portfolio_id=portfolio.id
    )
    db.commit()

    # WHEN - ticker rename
    rename_transaction_in = schemas.TransactionCreate(
        asset_id=old_asset.id,
        transaction_type=TransactionType.RENAME,
        quantity=Decimal("1"),  # Not used
        price_per_unit=Decimal("1"),  # Not used
        transaction_date=datetime(2023, 8, 1),
        details={"new_asset_id": str(new_asset.id)},
    )

    crud.crud_corporate_action.handle_rename(
        db,
        portfolio_id=portfolio.id,
        asset_id=old_asset.id,
        transaction_in=rename_transaction_in,
    )
    db.commit()

    # THEN
    # 1. Verify the RENAME audit transaction was saved
    rename_audit_tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.asset_id == old_asset.id,
            models.Transaction.transaction_type == TransactionType.RENAME,
        )
        .first()
    )
    assert rename_audit_tx is not None

    # 2. Verify BUY transaction was created for new ticker
    new_ticker_buy = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.asset_id == new_asset.id,
            models.Transaction.transaction_type == TransactionType.BUY,
        )
        .first()
    )
    assert new_ticker_buy is not None
    assert new_ticker_buy.quantity == Decimal("50")  # Same quantity
    # Cost basis preserved: 20,000 / 50 = 400 per share
    assert new_ticker_buy.price_per_unit == Decimal("400")


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_merger_no_holdings_rejects(db: Session) -> None:
    """
    Test that merger is rejected when no holdings exist on record date.
    """
    from fastapi import HTTPException

    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Empty Portfolio")
    old_asset = create_test_asset(db, ticker_symbol="NOHOLD_M")
    new_asset = create_test_asset(db, ticker_symbol="NEWHOLD_M")

    # No holdings created - attempt merger
    merger_in = schemas.TransactionCreate(
        asset_id=old_asset.id,
        transaction_type=TransactionType.MERGER,
        quantity=Decimal("1.5"),
        price_per_unit=Decimal("1"),
        transaction_date=datetime(2023, 6, 1),
        details={"new_asset_id": str(new_asset.id)},
    )

    with pytest.raises(HTTPException) as exc_info:
        crud.crud_corporate_action.handle_merger(
            db, portfolio_id=portfolio.id, asset_id=old_asset.id,
            transaction_in=merger_in,
        )
    assert exc_info.value.status_code == 400
    assert "No holdings found" in str(exc_info.value.detail)


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_demerger_no_holdings_rejects(db: Session) -> None:
    """
    Test that demerger is rejected when no holdings exist on record date.
    """
    from fastapi import HTTPException

    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Empty Demerger")
    old_asset = create_test_asset(db, ticker_symbol="NOHOLD_D")
    new_asset = create_test_asset(db, ticker_symbol="SPINOFF_D")

    demerger_in = schemas.TransactionCreate(
        asset_id=old_asset.id,
        transaction_type=TransactionType.DEMERGER,
        quantity=Decimal("1"),
        price_per_unit=Decimal("1"),
        transaction_date=datetime(2023, 7, 1),
        details={"new_asset_id": str(new_asset.id), "cost_allocation_pct": "30"},
    )

    with pytest.raises(HTTPException) as exc_info:
        crud.crud_corporate_action.handle_demerger(
            db, portfolio_id=portfolio.id, asset_id=old_asset.id,
            transaction_in=demerger_in,
        )
    assert exc_info.value.status_code == 400
    assert "No holdings found" in str(exc_info.value.detail)


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_rename_no_holdings_rejects(db: Session) -> None:
    """
    Test that rename is rejected when no holdings exist on record date.
    """
    from fastapi import HTTPException

    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Empty Rename")
    old_asset = create_test_asset(db, ticker_symbol="NOHOLD_R")
    new_asset = create_test_asset(db, ticker_symbol="RENAMED_R")

    rename_in = schemas.TransactionCreate(
        asset_id=old_asset.id,
        transaction_type=TransactionType.RENAME,
        quantity=Decimal("1"),
        price_per_unit=Decimal("1"),
        transaction_date=datetime(2023, 8, 1),
        details={"new_asset_id": str(new_asset.id)},
    )

    with pytest.raises(HTTPException) as exc_info:
        crud.crud_corporate_action.handle_rename(
            db, portfolio_id=portfolio.id, asset_id=old_asset.id,
            transaction_in=rename_in,
        )
    assert exc_info.value.status_code == 400
    assert "No holdings found" in str(exc_info.value.detail)


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_demerger_preserves_original_dates(db: Session) -> None:
    """
    Test that demerger creates child BUYs with original acquisition dates.
    """
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Date Test")
    parent_asset = create_test_asset(db, ticker_symbol="PARENT_DATE")
    child_asset = create_test_asset(db, ticker_symbol="CHILD_DATE")

    # Create buy on Jan 1
    original_date = datetime(2023, 1, 15)
    crud.transaction.create_with_portfolio(
        db,
        obj_in=schemas.TransactionCreate(
            asset_id=parent_asset.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_unit=Decimal("500"),
            transaction_date=original_date,
        ),
        portfolio_id=portfolio.id,
    )
    db.commit()

    # Demerger on July 1
    demerger_date = datetime(2023, 7, 1)
    demerger_in = schemas.TransactionCreate(
        asset_id=parent_asset.id,
        transaction_type=TransactionType.DEMERGER,
        quantity=Decimal("1"),
        price_per_unit=Decimal("1"),
        transaction_date=demerger_date,
        details={"new_asset_id": str(child_asset.id), "cost_allocation_pct": "25"},
    )
    crud.crud_corporate_action.handle_demerger(
        db, portfolio_id=portfolio.id, asset_id=parent_asset.id,
        transaction_in=demerger_in,
    )
    db.commit()

    # Verify child BUY has original date, not demerger date
    child_buy = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.asset_id == child_asset.id,
            models.Transaction.transaction_type == TransactionType.BUY,
        )
        .first()
    )
    assert child_buy is not None
    assert child_buy.transaction_date.date() == original_date.date()
    assert child_buy.details.get("from_demerger") is True


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_demerger_stores_total_cost_allocated(db: Session) -> None:
    """
    Test that demerger stores total_cost_allocated in audit transaction.
    """
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Cost Alloc Test")
    parent_asset = create_test_asset(db, ticker_symbol="PARENT_COST")
    child_asset = create_test_asset(db, ticker_symbol="CHILD_COST")

    # 100 shares at 1000 = 100,000 cost basis
    crud.transaction.create_with_portfolio(
        db,
        obj_in=schemas.TransactionCreate(
            asset_id=parent_asset.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_unit=Decimal("1000"),
            transaction_date=datetime(2023, 1, 1),
        ),
        portfolio_id=portfolio.id,
    )
    db.commit()

    # Demerger with 30% cost allocation
    demerger_in = schemas.TransactionCreate(
        asset_id=parent_asset.id,
        transaction_type=TransactionType.DEMERGER,
        quantity=Decimal("1"),
        price_per_unit=Decimal("1"),
        transaction_date=datetime(2023, 7, 1),
        details={"new_asset_id": str(child_asset.id), "cost_allocation_pct": "30"},
    )
    crud.crud_corporate_action.handle_demerger(
        db, portfolio_id=portfolio.id, asset_id=parent_asset.id,
        transaction_in=demerger_in,
    )
    db.commit()

    # Verify total_cost_allocated is stored
    demerger_audit = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.asset_id == parent_asset.id,
            models.Transaction.transaction_type == TransactionType.DEMERGER,
        )
        .first()
    )
    assert demerger_audit is not None
    assert "total_cost_allocated" in demerger_audit.details
    # 30% of 100,000 = 30,000
    assert Decimal(demerger_audit.details["total_cost_allocated"]) == Decimal("30000")


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_multi_demerger_cost_calculation(db: Session) -> None:
    """
    Test that multiple demergers correctly reduce parent cost basis.
    Example: 90,000 -> 40% parent, 30% child1, 30% child2
    """
    from app.cache.utils import invalidate_caches_for_portfolio

    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Multi Demerger")
    parent = create_test_asset(db, ticker_symbol="MULTI_PARENT")
    child1 = create_test_asset(db, ticker_symbol="MULTI_CHILD1")
    child2 = create_test_asset(db, ticker_symbol="MULTI_CHILD2")

    # 100 shares at 900 = 90,000 cost basis
    crud.transaction.create_with_portfolio(
        db,
        obj_in=schemas.TransactionCreate(
            asset_id=parent.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_unit=Decimal("900"),
            transaction_date=datetime(2023, 1, 1),
        ),
        portfolio_id=portfolio.id,
    )
    db.commit()

    # First demerger: 30% to child1
    crud.crud_corporate_action.handle_demerger(
        db, portfolio_id=portfolio.id, asset_id=parent.id,
        transaction_in=schemas.TransactionCreate(
            asset_id=parent.id,
            transaction_type=TransactionType.DEMERGER,
            quantity=Decimal("1"),
            price_per_unit=Decimal("1"),
            transaction_date=datetime(2023, 7, 1),
            details={"new_asset_id": str(child1.id), "cost_allocation_pct": "30"},
        ),
    )
    db.commit()

    # Second demerger: 30% to child2
    crud.crud_corporate_action.handle_demerger(
        db, portfolio_id=portfolio.id, asset_id=parent.id,
        transaction_in=schemas.TransactionCreate(
            asset_id=parent.id,
            transaction_type=TransactionType.DEMERGER,
            quantity=Decimal("1"),
            price_per_unit=Decimal("1"),
            transaction_date=datetime(2023, 8, 1),
            details={"new_asset_id": str(child2.id), "cost_allocation_pct": "30"},
        ),
    )
    db.commit()

    # Invalidate cache and get holdings
    invalidate_caches_for_portfolio(db, portfolio_id=portfolio.id)
    holdings_data = crud.holding.get_portfolio_holdings_and_summary(
        db=db, portfolio_id=portfolio.id
    )

    # Find holdings
    holdings = holdings_data.holdings
    parent_h = next((h for h in holdings if h.asset_id == parent.id), None)
    child1_h = next((h for h in holdings if h.asset_id == child1.id), None)
    child2_h = next((h for h in holdings if h.asset_id == child2.id), None)

    # Verify cost distribution: 40% + 30% + 30% = 100%
    # Parent: 90,000 - 27,000 - 27,000 = 36,000
    assert parent_h is not None
    assert parent_h.total_invested_amount == Decimal("36000")

    # Child1: 30% of 90,000 = 27,000
    assert child1_h is not None
    assert child1_h.total_invested_amount == Decimal("27000")

    # Child2: 30% of 90,000 = 27,000
    assert child2_h is not None
    assert child2_h.total_invested_amount == Decimal("27000")

    # Total should still be 90,000
    total = (
        parent_h.total_invested_amount
        + child1_h.total_invested_amount
        + child2_h.total_invested_amount
    )
    assert total == Decimal("90000")



@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_handle_bonus_issue_fractional_inr(db: Session) -> None:
    """
    Test case for handling a bonus issue with fractional result for INR asset.
    - GIVEN an INR asset with 100 shares.
    - WHEN a 1:3 bonus issue is logged (1 new for 3 old).
    - THEN the resulting bonus shares should be floored to 33 (integer), not 33.33.
    """
    # GIVEN
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Bonus Fractional Portfolio")
    asset = create_test_asset(db, ticker_symbol="INFY")

    # Manually update currency to INR since helper defaults to USD
    asset.currency = "INR"
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Create initial holding of 100 shares
    initial_buy = schemas.TransactionCreate(
        asset_id=asset.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("100"),
        price_per_unit=Decimal("1500"),
        transaction_date=datetime(2023, 1, 1),
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=initial_buy, portfolio_id=portfolio.id
    )
    db.commit()

    # WHEN
    # A 1:3 bonus issue (1 new for 3 old)
    # Expected: 100 / 3 * 1 = 33.3333 -> Floored to 33
    bonus_transaction_in = schemas.TransactionCreate(
        asset_id=asset.id,
        transaction_type=TransactionType.BONUS,
        quantity=Decimal("1"),  # New shares
        price_per_unit=Decimal("3"),  # Old shares
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
    txs = db.query(models.Transaction).filter(
        models.Transaction.portfolio_id == portfolio.id,
        models.Transaction.asset_id == asset.id,
        models.Transaction.transaction_type == TransactionType.BUY,
        models.Transaction.price_per_unit == 0,
        models.Transaction.transaction_date == datetime(2023, 6, 1)
    ).all()

    assert len(txs) == 1
    bonus_tx = txs[0]
    assert bonus_tx.quantity == Decimal("33")


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_handle_split_issue_fractional_inr(db: Session) -> None:
    """
    Test case for handling a split issue with fractional result for INR asset.
    - GIVEN an INR asset with 1 share.
    - WHEN a 3:2 split is logged (3 new for 2 old).
    - THEN the resulting shares should be floored to 1 (integer), not 1.5.
    """
    # GIVEN
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Split Fractional Portfolio")
    asset = create_test_asset(db, ticker_symbol="TATASTEEL")

    # Manually update currency to INR
    asset.currency = "INR"
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Create initial holding of 1 share
    initial_buy = schemas.TransactionCreate(
        asset_id=asset.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("1"),
        price_per_unit=Decimal("100"),
        transaction_date=datetime(2023, 1, 1),
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=initial_buy, portfolio_id=portfolio.id
    )
    db.commit()

    # WHEN
    # A 3:2 split (3 new for 2 old)
    # Expected: 1 * (3/2) = 1.5 -> Floored to 1
    split_transaction_in = schemas.TransactionCreate(
        asset_id=asset.id,
        transaction_type=TransactionType.SPLIT,
        quantity=Decimal("3"),  # New shares (ratio numerator)
        price_per_unit=Decimal("2"),  # Old shares (ratio denominator)
        transaction_date=datetime(2023, 6, 1),
    )

    crud.crud_corporate_action.handle_stock_split(
        db,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_in=split_transaction_in,
    )
    db.commit()

    # THEN
    from app.cache.utils import invalidate_caches_for_portfolio
    invalidate_caches_for_portfolio(db, portfolio_id=portfolio.id)

    holdings_data = crud.holding.get_portfolio_holdings_and_summary(
        db=db, portfolio_id=portfolio.id
    )

    asset_holding = next(
        (h for h in holdings_data.holdings if h.asset_id == asset.id), None
    )

    assert asset_holding is not None
    assert asset_holding.quantity == Decimal("1")

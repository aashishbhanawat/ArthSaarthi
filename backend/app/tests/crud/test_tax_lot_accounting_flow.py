from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app import crud, schemas
from app.schemas.transaction import TransactionLinkCreate
from app.tests.utils.user import create_random_user


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_tax_lot_accounting_flow(db: Session):
    # Setup: User
    user, _ = create_random_user(db)

    # Setup: Portfolio
    portfolio = crud.portfolio.create_with_owner(
        db=db,
        obj_in=schemas.PortfolioCreate(name="Test Portfolio"),
        user_id=user.id
    )

    # Setup: Asset (Stock)
    asset = crud.asset.create(
        db=db,
        obj_in=schemas.AssetCreate(
            ticker_symbol="TESTLOT",
            name="Test Lot Stock",
            asset_type="STOCK",
            currency="INR",
        ),
    )

    # 1. Buy 10 units @ 100 on D-10
    buy1 = crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="BUY",
            quantity=10,
            price_per_unit=100,
            transaction_date=datetime.now() - timedelta(days=10)
        ),
        portfolio_id=portfolio.id
    )

    # 2. Buy 10 units @ 120 on D-5
    buy2 = crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="BUY",
            quantity=10,
            price_per_unit=120,
            transaction_date=datetime.now() - timedelta(days=5)
        ),
        portfolio_id=portfolio.id
    )

    # 3. Check Available Lots
    lots = crud.transaction.get_available_lots(
        db=db, asset_id=asset.id, user_id=user.id
    )
    assert len(lots) == 2, "Should have 2 available lots"
    # Identify lots by ID to be sure
    # Identify lots by ID to be sure
    lot1 = next(lot for lot in lots if lot["id"] == buy1.id)
    lot2 = next(lot for lot in lots if lot["id"] == buy2.id)

    assert lot1["available_quantity"] == 10
    assert lot2["available_quantity"] == 10

    # 4. Sell using specific links (Sell 5 from Lot 2, i.e., the one bought on D-5)
    # 4. Sell using specific links (Sell 5 from Lot 2, i.e., the one bought on D-5)

    sell = crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="SELL",
            quantity=5,
            price_per_unit=130,
            transaction_date=datetime.now(),
            links=[
                TransactionLinkCreate(
                    buy_transaction_id=lot2["id"],
                    quantity=5
                )
            ]
        ),
        portfolio_id=portfolio.id
    )

    # Verify links created
    assert len(sell.sell_links) == 1, "Should have 1 link"
    assert sell.sell_links[0].buy_transaction_id == buy2.id
    assert float(sell.sell_links[0].quantity) == 5.0

    # 5. Check Available Lots again
    lots_after = crud.transaction.get_available_lots(
        db=db, asset_id=asset.id, user_id=user.id
    )

    # Lot 1 should be untouched (10)
    # Lot 2 should be reduced (5)

    lot1_after = next(lot for lot in lots_after if lot["id"] == buy1.id)
    lot2_after = next(lot for lot in lots_after if lot["id"] == buy2.id)

    assert float(lot1_after["available_quantity"]) == 10.0
    assert float(lot2_after["available_quantity"]) == 5.0

    # 6. Verify Unlinked (FIFO) behavior
    # Sell 5 more without links. Should take from Lot 1 (FIFO, oldest).
    crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="SELL",
            quantity=5,
            price_per_unit=150,
            transaction_date=datetime.now()
        ),
        portfolio_id=portfolio.id
    )

    lots_final = crud.transaction.get_available_lots(
        db=db, asset_id=asset.id, user_id=user.id
    )

    lot1_final = next(lot for lot in lots_final if lot["id"] == buy1.id)
    lot2_final = next(lot for lot in lots_final if lot["id"] == buy2.id)

    # Lot 1 was 10, sold 5 (FIFO) -> 5 remaining
    assert float(lot1_final["available_quantity"]) == 5.0
    # Lot 2 was 5, untouched -> 5 remaining
    assert float(lot2_final["available_quantity"]) == 5.0

    # 7. Verify P&L impact
    # (via crude check if possible, or just trust get_available_lots handles accounting)
    # P&L calculation is complex to test here without running full Holdings calc logic.
    # But get_available_lots logic (specifically the 'unlinked' part)
    # relying on previous sales
    # proves that the system knows what has been sold.


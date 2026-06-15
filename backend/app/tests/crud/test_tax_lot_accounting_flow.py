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


def test_tax_lot_split_adjustment(db: Session):
    # Setup: User
    user, _ = create_random_user(db)

    # Setup: Portfolio
    portfolio = crud.portfolio.create_with_owner(
        db=db,
        obj_in=schemas.PortfolioCreate(name="Split Test Portfolio"),
        user_id=user.id
    )

    # Setup: Asset (USD Stock, so no flooring)
    asset = crud.asset.create(
        db=db,
        obj_in=schemas.AssetCreate(
            ticker_symbol="SPLITLOT",
            name="Split Lot Stock",
            asset_type="STOCK",
            currency="USD",
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

    # 3. Perform a 2-for-1 stock split on D-3
    crud.crud_corporate_action.handle_stock_split(
        db=db,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="SPLIT",
            quantity=2,  # New
            price_per_unit=1,  # Old
            transaction_date=datetime.now() - timedelta(days=3)
        )
    )

    # 4. Check Available Lots
    lots = crud.transaction.get_available_lots(
        db=db, asset_id=asset.id, user_id=user.id
    )
    assert len(lots) == 2, "Should have 2 available lots"
    lot1 = next(lot for lot in lots if lot["id"] == buy1.id)
    lot2 = next(lot for lot in lots if lot["id"] == buy2.id)

    # Verify that quantities are doubled and prices are halved
    assert float(lot1["available_quantity"]) == 20.0
    assert float(lot1["price_per_unit"]) == 50.0
    assert float(lot2["available_quantity"]) == 20.0
    assert float(lot2["price_per_unit"]) == 60.0

    # 5. Sell 15 units. FIFO should consume from Lot 1 (which now has 20 units)
    crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="SELL",
            quantity=15,
            price_per_unit=70,
            transaction_date=datetime.now()
        ),
        portfolio_id=portfolio.id
    )

    lots_after = crud.transaction.get_available_lots(
        db=db, asset_id=asset.id, user_id=user.id
    )
    lot1_after = next(lot for lot in lots_after if lot["id"] == buy1.id)
    lot2_after = next(lot for lot in lots_after if lot["id"] == buy2.id)

    # Lot 1 was 20, sold 15 -> 5 remaining
    assert float(lot1_after["available_quantity"]) == 5.0
    # Lot 2 remains untouched at 20
    assert float(lot2_after["available_quantity"]) == 20.0


def test_tax_lot_split_inr_flooring(db: Session):
    # Setup: User
    user, _ = create_random_user(db)

    # Setup: Portfolio
    portfolio = crud.portfolio.create_with_owner(
        db=db,
        obj_in=schemas.PortfolioCreate(name="Split INR Portfolio"),
        user_id=user.id
    )

    # Setup: Asset (INR Stock, floors fractional shares)
    asset = crud.asset.create(
        db=db,
        obj_in=schemas.AssetCreate(
            ticker_symbol="INRSLOT",
            name="INR Split Stock",
            asset_type="STOCK",
            currency="INR",
        ),
    )

    # 1. Buy 1 unit @ 100 on D-10
    crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="BUY",
            quantity=1,
            price_per_unit=100,
            transaction_date=datetime.now() - timedelta(days=10)
        ),
        portfolio_id=portfolio.id
    )

    # 2. Perform a 3:2 stock split on D-5 (3 new for 2 old)
    # 1 share * 1.5 ratio = 1.5 shares -> floored to 1 share in INR
    crud.crud_corporate_action.handle_stock_split(
        db=db,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="SPLIT",
            quantity=3,  # New
            price_per_unit=2,  # Old
            transaction_date=datetime.now() - timedelta(days=5)
        )
    )

    # 3. Check Available Lots
    lots = crud.transaction.get_available_lots(
        db=db, asset_id=asset.id, user_id=user.id
    )
    assert len(lots) == 1, "Should have 1 available lot"
    lot1 = lots[0]

    # Verify that the lot quantity is floored to 1.0 (originally 1.5 before flooring)
    assert float(lot1["available_quantity"]) == 1.0
    # Price per unit is adjusted: 100 / 1.5 = 66.6666...
    assert abs(float(lot1["price_per_unit"]) - (100.0 / 1.5)) < 0.01



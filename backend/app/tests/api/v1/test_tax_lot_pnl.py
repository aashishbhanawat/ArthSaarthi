from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app import crud, schemas
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_specific_lot_pnl_calculation(db: Session):
    # 1. Setup User & Portfolio
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db=db, user_id=user.id, name="Test Portfolio")

    # 2. Create Asset
    asset_ticker = "LOTT"
    asset = crud.asset.create(db, obj_in=schemas.AssetCreate(
        ticker_symbol=asset_ticker,
        name="Lot Test Tech",
        asset_type="Stock",
        currency="USD"
    ))

    # 3. Buy Lot 1: 10 @ $100
    crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="BUY",
            quantity=Decimal("10"),
            price_per_unit=Decimal("100"),
            transaction_date="2023-01-01T00:00:00Z"
        ),
        portfolio_id=portfolio.id
    )

    # 4. Buy Lot 2: 10 @ $200
    buy2 = crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="BUY",
            quantity=Decimal("10"),
            price_per_unit=Decimal("200"),
            transaction_date="2023-01-05T00:00:00Z"
        ),
        portfolio_id=portfolio.id
    )

    # 5. Sell 5 units - LINKED to Lot 2 (Higher Cost)
    # This should result in Realized P&L based on Cost $200
    # Sell Price = $250.
    # Expected Realized P&L = (250 - 200) * 5 = 250.

    # If it was FIFO (Avg Cost fallback or default), it would take Lot 1 ($100).
    # Expected P&L (FIFO) = (250 - 100) * 5 = 750.

    sell_price = Decimal("250")
    sell_qty = Decimal("5")

    # Create Link Object
    link_in = schemas.TransactionLinkCreate(
        buy_transaction_id=buy2.id,
        quantity=sell_qty
    )

    # Create Sell Transaction with Links
    sell_tx = crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=asset.id,
            transaction_type="SELL",
            quantity=sell_qty,
            price_per_unit=sell_price,
            transaction_date="2023-01-10T00:00:00Z",
            links=[link_in]
        ),
        portfolio_id=portfolio.id
    )

    # 6. Verify Creation
    assert len(sell_tx.sell_links) == 1
    assert sell_tx.sell_links[0].buy_transaction_id == buy2.id

    # 7. Verify P&L Calculation (via Holdings)
    # We need to trigger the holdings calculation which includes realized
    # P&L processing.
    from app.cache.utils import invalidate_caches_for_portfolio
    invalidate_caches_for_portfolio(db, portfolio_id=portfolio.id)

    holdings_data = crud.holding.get_portfolio_holdings_and_summary(
        db=db, portfolio_id=portfolio.id
    )

    # Check Portfolio Level Realized P&L
    # Total P&L should be exactly 250.
    assert holdings_data.summary.total_realized_pnl == Decimal("250")

    # Also verify remaining holdings
    # Should have 15 units remaining (10 from Lot 1, 5 from Lot 2)
    # Cost Basis?
    # Lot 1: 10 * 100 = 1000
    # Lot 2: 5 * 200 = 1000
    # Total Value (Cost) = 2000.
    # Avg Cost = 2000 / 15 = 133.3333

    asset_holding = next(
        h for h in holdings_data.holdings if h.asset_id == asset.id
    )
    assert asset_holding.quantity == Decimal("15")
    # Verify average buy price matches expected remaining lots
    expected_avg = Decimal("2000") / Decimal("15")
    assert abs(asset_holding.average_buy_price - expected_avg) < Decimal("0.01")

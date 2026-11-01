from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.tests.utils.user import create_random_user


def test_get_multi_by_asset_filters_by_user_id(db: Session) -> None:
    """Regression test: get_multi_by_asset must not leak cross-tenant transactions."""
    # Setup: two users, same shared asset, each with their own transactions
    user_a, _ = create_random_user(db)
    user_b, _ = create_random_user(db)
    portfolio_a = create_test_portfolio(db, user_id=user_a.id, name="A")
    portfolio_b = create_test_portfolio(db, user_id=user_b.id, name="B")
    shared_asset = create_test_asset(db, ticker_symbol="SHARED")

    txn_a = create_test_transaction(db, portfolio_id=portfolio_a.id, asset_id=shared_asset.id)
    txn_b = create_test_transaction(db, portfolio_id=portfolio_b.id, asset_id=shared_asset.id)

    # Assert: user A sees only their own transaction
    results_a = crud.transaction.get_multi_by_asset(db, asset_id=shared_asset.id, user_id=user_a.id)
    assert len(results_a) == 1
    assert results_a[0].id == txn_a.id

    # Assert: user B sees only their own transaction
    results_b = crud.transaction.get_multi_by_asset(db, asset_id=shared_asset.id, user_id=user_b.id)
    assert len(results_b) == 1
    assert results_b[0].id == txn_b.id

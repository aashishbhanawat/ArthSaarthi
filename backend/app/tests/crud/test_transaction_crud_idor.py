import pytest
from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")

def test_get_multi_by_asset_filters_by_user_id(db: Session) -> None:
    """Regression test: get_multi_by_asset must not leak cross-tenant transactions."""
    # Setup: two users, same shared asset, each with their own transactions
    # Note: create_random_user creates a user but it requires master key to be loaded
    # and settings.DEPLOYMENT_MODE might be postgres.
    # Actually, if we just use normal text for fields it might bypass encryption
    # depending on how test runner sets up things. Let's just create raw users to avoid
    # the security dependency which breaks when master key is not loaded in Postgres CI mode.

    import random
    import uuid

    from app.models.user import User

    user_a = User(id=uuid.uuid4(), email=f"usera{random.randint(1,1000)}@test.com", hashed_password="pw", full_name="User A", is_admin=False)
    user_b = User(id=uuid.uuid4(), email=f"userb{random.randint(1,1000)}@test.com", hashed_password="pw", full_name="User B", is_admin=False)
    db.add(user_a)
    db.add(user_b)
    db.commit()

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

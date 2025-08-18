import pytest
from sqlalchemy.orm import Session

from app import crud
from app.schemas.asset_alias import AssetAliasCreate
from app.tests.utils.asset import create_test_asset
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_create_and_get_asset_alias(db: Session) -> None:
    """
    Test creating a new asset alias and retrieving it by its alias symbol.
    """
    # 1. Setup: Create a user and an asset to associate the alias with
    user, _ = create_random_user(db)
    asset = create_test_asset(db, ticker_symbol="TESTASSET", name="Test Asset")
    alias_symbol = "MYALIAS"

    # 2. Create the alias
    alias_in = AssetAliasCreate(
        alias_symbol=alias_symbol,
        asset_id=asset.id,
        user_id=user.id,
        source="test",
    )
    created_alias = crud.asset_alias.create(db=db, obj_in=alias_in)
    db.commit()

    # 3. Retrieve the alias using the new method
    retrieved_alias = crud.asset_alias.get_by_alias(
        db=db, alias_symbol=alias_symbol, source="test"
    )

    # 4. Assertions
    assert retrieved_alias is not None
    assert retrieved_alias.id == created_alias.id
    assert retrieved_alias.alias_symbol == alias_symbol
    assert retrieved_alias.asset_id == asset.id


def test_get_asset_alias_not_found(db: Session) -> None:
    """
    Test retrieving a non-existent asset alias.
    """
    # 1. Attempt to retrieve an alias that does not exist
    retrieved_alias = crud.asset_alias.get_by_alias(
        db=db, alias_symbol="NONEXISTENTALIAS", source="test"
    )

    # 2. Assertion
    assert retrieved_alias is None

"""Tests for ICICI ShortName alias creation during asset seeding (#216)."""
import pandas as pd
import pytest
from sqlalchemy.orm import Session

from app import crud
from app.services.asset_seeder import AssetSeeder


@pytest.fixture()
def seeder(db: Session):
    """Create a fresh AssetSeeder instance."""
    return AssetSeeder(db=db, debug=True)


# ------------------------------------------------------------------ #
#  _process_fallback_row  →  alias creation
# ------------------------------------------------------------------ #

def test_alias_created_when_shortname_differs(
    seeder: AssetSeeder,
    db: Session,
):
    """ShortName ≠ ExchangeCode → alias should be created."""
    row = pd.Series({
        "ExchangeCode": "HDFCAMC",
        "CompanyName": "HDFC Asset Mgmt",
        "ISINCode": "INE127TEST01",
        "Series": "EQ",
        "ShortName": "HDFCAMC-EQ",
    })
    seeder._process_fallback_row(row)
    seeder.flush_pending()
    db.commit()

    # Asset should exist
    asset = crud.asset.get_by_ticker(db, ticker_symbol="HDFCAMC")
    assert asset is not None

    # Alias should exist
    alias = crud.asset_alias.get_by_alias(
        db,
        alias_symbol="HDFCAMC-EQ",
        source="ICICI Direct Tradebook",
    )
    assert alias is not None
    assert alias.asset_id == asset.id
    assert seeder.alias_count == 1


def test_no_alias_when_shortname_matches_ticker(
    seeder: AssetSeeder,
    db: Session,
):
    """ShortName == ticker (case-insensitive) → no alias."""
    row = pd.Series({
        "ExchangeCode": "RELIANCE",
        "CompanyName": "Reliance Industries",
        "ISINCode": "INE002TEST01",
        "Series": "EQ",
        "ShortName": "RELIANCE",
    })
    seeder._process_fallback_row(row)
    seeder.flush_pending()
    db.commit()

    assert seeder.alias_count == 0


def test_no_alias_when_shortname_missing(
    seeder: AssetSeeder,
    db: Session,
):
    """Missing ShortName column → no alias, no error."""
    row = pd.Series({
        "ExchangeCode": "TCS",
        "CompanyName": "Tata Consultancy",
        "ISINCode": "INE003TEST01",
        "Series": "EQ",
        # ShortName intentionally absent
    })
    seeder._process_fallback_row(row)
    seeder.flush_pending()
    db.commit()

    assert seeder.alias_count == 0


def test_no_alias_when_shortname_nan(
    seeder: AssetSeeder,
    db: Session,
):
    """ShortName is NaN → no alias."""
    row = pd.Series({
        "ExchangeCode": "INFY",
        "CompanyName": "Infosys Ltd",
        "ISINCode": "INE004TEST01",
        "Series": "EQ",
        "ShortName": float("nan"),
    })
    seeder._process_fallback_row(row)
    seeder.flush_pending()
    db.commit()

    assert seeder.alias_count == 0


def test_duplicate_alias_not_created_on_reseed(
    seeder: AssetSeeder,
    db: Session,
):
    """Re-seeding the same row should not create a duplicate alias."""
    row = pd.Series({
        "ExchangeCode": "SBIN",
        "CompanyName": "State Bank of India",
        "ISINCode": "INE005TEST01",
        "Series": "EQ",
        "ShortName": "SBI",
    })
    seeder._process_fallback_row(row)
    seeder.flush_pending()
    db.commit()
    assert seeder.alias_count == 1

    # Create a second seeder (simulates re-seed)
    seeder2 = AssetSeeder(db=db, debug=True)
    # Row won't create asset (ticker exists), so alias
    # path won't be reached via _process_fallback_row.
    # Instead, verify alias dedup via _create_alias directly.
    asset = crud.asset.get_by_ticker(db, ticker_symbol="SBIN")
    result = seeder2._create_alias(
        alias_symbol="SBI",
        source="ICICI Direct Tradebook",
        asset_id=asset.id,
    )
    assert result is False  # Already exists
    assert seeder2.alias_count == 0

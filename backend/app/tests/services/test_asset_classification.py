from datetime import date

import pandas as pd
import pytest
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.bond import Bond
from app.schemas.enums import BondType
from app.services.asset_seeder import AssetSeeder


@pytest.fixture()
def seeder(db: Session):
    """Create a fresh AssetSeeder instance."""
    return AssetSeeder(db=db, debug=True)


def test_classify_stock_series_nse(seeder: AssetSeeder, db: Session):
    """NSE fallback row with stock series (EQ, BE, SM, ST) should be classified
    as STOCK.
    """
    rows = [
        pd.Series({
            "ExchangeCode": "INFY",
            "CompanyName": "Infosys Limited",
            "ISINCode": "INE009A01021",
            "Series": "EQ",
        }),
        pd.Series({
            "ExchangeCode": "BE_STOCK",
            "CompanyName": "BE Stock Company",
            "ISINCode": "INE009A01022",
            "Series": "BE",
        }),
        pd.Series({
            "ExchangeCode": "SM_STOCK",
            "CompanyName": "SM Stock Company",
            "ISINCode": "INE009A01023",
            "Series": "SM",
        }),
        pd.Series({
            "ExchangeCode": "ST_STOCK",
            "CompanyName": "ST Stock Company",
            "ISINCode": "INE009A01024",
            "Series": "ST",
        })
    ]

    for row in rows:
        seeder._process_fallback_row(row, exchange="NSE")

    seeder.flush_pending()
    db.commit()

    for ticker in ["INFY", "BE_STOCK", "SM_STOCK", "ST_STOCK"]:
        asset = db.query(Asset).filter_by(ticker_symbol=ticker).first()
        assert asset is not None
        assert asset.asset_type == "STOCK"


def test_classify_bond_series_nse(seeder: AssetSeeder, db: Session):
    """NSE fallback rows with bond-like series should be classified as BOND."""
    rows = [
        # Sovereign Gold Bond
        pd.Series({
            "ExchangeCode": "SGBDEC30",
            "CompanyName": "SGB 2.50% DEC 2030",
            "ISINCode": "IN0020200012",
            "Series": "GB",
        }),
        # Govt Security
        pd.Series({
            "ExchangeCode": "718GS2033",
            "CompanyName": "7.18% GS 2033",
            "ISINCode": "IN0020230085",
            "Series": "GS",
        }),
        # Corporate NCD
        pd.Series({
            "ExchangeCode": "HUDCO-N2",
            "CompanyName": "HUDCO N2 BOND",
            "ISINCode": "INE123A07011",
            "Series": "N2",
        })
    ]

    for row in rows:
        seeder._process_fallback_row(row, exchange="NSE")

    seeder.flush_pending()
    db.commit()

    sgb = db.query(Asset).filter_by(ticker_symbol="SGBDEC30").first()
    assert sgb is not None
    assert sgb.asset_type == "BOND"
    assert sgb.bond is not None
    assert sgb.bond.bond_type == BondType.SGB

    gs = db.query(Asset).filter_by(ticker_symbol="718GS2033").first()
    assert gs is not None
    assert gs.asset_type == "BOND"
    assert gs.bond is not None
    assert gs.bond.bond_type == BondType.GOVERNMENT

    hudco = db.query(Asset).filter_by(ticker_symbol="HUDCO-N2").first()
    assert hudco is not None
    assert hudco.asset_type == "BOND"
    assert hudco.bond is not None
    assert hudco.bond.bond_type == BondType.CORPORATE


def test_isin_mapping_cross_exchange(seeder: AssetSeeder, db: Session):
    """BSE fallback row with series 'DR' but present in nse_series_map as 'EQ'
    should be classified as STOCK.
    """
    # Seed the NSE series map first
    seeder.nse_series_map["INE203G01027"] = "EQ"
    seeder.nse_series_map["INE885A01032"] = "EQ"

    # Process BSE fallback rows
    row_igl = pd.Series({
        "ScripID": "IGL",
        "ScripName": "INDRAPRASHTHA GAS LTD",
        "ISINCode": "INE203G01027",
        "Series": "DR",
    })
    row_amara = pd.Series({
        "ScripID": "ARE&M",
        "ScripName": "AMARA RAJA ENERGY & MOBILITY",
        "ISINCode": "INE885A01032",
        "Series": "DR",
    })

    seeder._process_fallback_row(row_igl, exchange="BSE")
    seeder._process_fallback_row(row_amara, exchange="BSE")

    seeder.flush_pending()
    db.commit()

    igl = db.query(Asset).filter_by(ticker_symbol="IGL").first()
    assert igl is not None
    assert igl.asset_type == "STOCK"

    amara = db.query(Asset).filter_by(ticker_symbol="ARE&M").first()
    assert amara is not None
    assert amara.asset_type == "STOCK"


def test_bse_series_c_stock(seeder: AssetSeeder, db: Session):
    """BSE fallback row with Series C should be classified as STOCK."""
    row = pd.Series({
        "ScripID": "BSE_C_STOCK",
        "ScripName": "7NR RETAIL LIMITED",
        "ISINCode": "INE413X01035",
        "Series": "C",
    })
    seeder._process_fallback_row(row, exchange="BSE")
    seeder.flush_pending()
    db.commit()

    asset = db.query(Asset).filter_by(ticker_symbol="BSE_C_STOCK").first()
    assert asset is not None
    assert asset.asset_type == "STOCK"


def test_refined_month_heuristic(seeder: AssetSeeder):
    """Verify that month-like substrings inside words do not trigger
    bond classification.
    """
    # INDRAPRASHTHA has "APR", AMARA has "MAR", KUMAR has "MAR"
    test_cases = [
        ("IGL", "INDRAPRASHTHA GAS LTD", "DR"),
        ("AMARAJ", "AMARA RAJA ENERGY & MOBILITY", "DR"),
        ("KUMAR", "KUMAR WIRE CLOTH", "DR")
    ]
    for ticker, name, series in test_cases:
        asset_type, bond_type = seeder._classify_asset_heuristic(ticker, name, series)
        # Should not be classified as BOND
        assert asset_type is None
        assert bond_type is None

    # Real bonds should still be classified as BOND
    bond_cases = [
        ("HUDCO", "HUDCO TAX FREE BOND DEC 2028", "DR"),
        ("NHAI", "NHAI TAX FREE BOND 15-JAN-25", "DR"),
        ("SGB", "SGB 2.5% 25JAN26", "DR")
    ]
    for ticker, name, series in bond_cases:
        asset_type, bond_type = seeder._classify_asset_heuristic(ticker, name, series)
        assert asset_type == "BOND"
        assert bond_type == BondType.CORPORATE or bond_type == BondType.SGB


def test_auto_correction_of_misclassified_bonds(db: Session):
    """Verify that previously misclassified BOND assets (e.g. IGL with
    month-like substring) are automatically corrected to STOCK and their
    linked Bond records are deleted.
    """
    # 1. Create a misclassified asset in the database manually
    asset_igl = Asset(
        ticker_symbol="IGL_TEST",
        name="INDRAPRASHTHA GAS LTD",
        asset_type="BOND",
        currency="INR",
        exchange="BSE",
        isin="INE203G01027_TEST"
    )
    db.add(asset_igl)
    db.commit()

    # 2. Create the associated Bond record
    bond_igl = Bond(
        asset_id=asset_igl.id,
        bond_type=BondType.CORPORATE,
        isin="INE203G01027_TEST",
        maturity_date=date(2030, 1, 1)
    )
    db.add(bond_igl)
    db.commit()

    # 3. Create a legitimate bond to verify it's NOT touched
    asset_sgb = Asset(
        ticker_symbol="SGB_TEST",
        name="SGB 2.5% 25JAN26",
        asset_type="BOND",
        currency="INR",
        exchange="BSE",
        isin="IN0020200012_TEST"
    )
    db.add(asset_sgb)
    db.commit()

    bond_sgb = Bond(
        asset_id=asset_sgb.id,
        bond_type=BondType.SGB,
        isin="IN0020200012_TEST",
        maturity_date=date(2026, 1, 25)
    )
    db.add(bond_sgb)
    db.commit()

    # 4. Initialize AssetSeeder, which calls _load_existing_assets
    # and _fix_misclassified_bonds
    try:
        AssetSeeder(db=db, debug=True)

        # 5. Assertions
        # IGL should be corrected to STOCK
        db.refresh(asset_igl)
        assert asset_igl.asset_type == "STOCK"

        # Linked Bond for IGL should be deleted
        associated_bond_igl = (
            db.query(Bond.id).filter_by(asset_id=asset_igl.id).first()
        )
        assert associated_bond_igl is None

        # SGB should remain a BOND
        db.refresh(asset_sgb)
        assert asset_sgb.asset_type == "BOND"
        associated_bond_sgb = (
            db.query(Bond.id).filter_by(asset_id=asset_sgb.id).first()
        )
        assert associated_bond_sgb is not None
    finally:
        # Cleanup test data safely
        for b in db.query(Bond).filter(
            Bond.isin.in_(["INE203G01027_TEST", "IN0020200012_TEST"])
        ).all():
            db.delete(b)
        for a in db.query(Asset).filter(
            Asset.isin.in_(["INE203G01027_TEST", "IN0020200012_TEST"])
        ).all():
            db.delete(a)
        db.commit()


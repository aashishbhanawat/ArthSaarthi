from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app import crud, schemas
from app.schemas.bond import BondCreate, BondUpdate
from app.schemas.enums import BondType, PaymentFrequency
from app.tests.utils.utils import random_lower_string


def test_create_bond(db: Session) -> None:
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type="BOND",
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id,
        bond_type=BondType.CORPORATE,
        face_value=Decimal("1000.00"),
        coupon_rate=Decimal("7.5"),
        maturity_date=date(2030, 1, 1),
        isin="INE123456789",
        payment_frequency=PaymentFrequency.SEMI_ANNUALLY,
        first_payment_date=date(2025, 7, 1),
    )
    bond = crud.bond.create(db=db, obj_in=bond_in)
    assert bond.asset_id == asset.id
    assert bond.bond_type == "CORPORATE"
    assert bond.face_value == Decimal("1000.00")
    assert bond.coupon_rate == Decimal("7.5")
    assert bond.maturity_date == date(2030, 1, 1)


def test_get_bond(db: Session) -> None:
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type="BOND",
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id,
        bond_type=BondType.GOVERNMENT,
        maturity_date=date(2035, 1, 1),
    )
    bond = crud.bond.create(db=db, obj_in=bond_in)
    stored_bond = crud.bond.get(db=db, id=bond.id)
    assert stored_bond
    assert stored_bond.id == bond.id
    assert stored_bond.asset_id == asset.id


def test_update_bond(db: Session) -> None:
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type="BOND",
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id,
        bond_type=BondType.CORPORATE,
        maturity_date=date(2030, 1, 1),
        coupon_rate=Decimal("8.0"),
    )
    bond = crud.bond.create(db=db, obj_in=bond_in)
    bond_update = BondUpdate(coupon_rate=Decimal("8.25"), **bond_in.model_dump(exclude={"coupon_rate", "asset_id"}))
    bond2 = crud.bond.update(db=db, db_obj=bond, obj_in=bond_update)
    assert bond2.id == bond.id
    assert bond2.coupon_rate == Decimal("8.25")


def test_delete_bond(db: Session) -> None:
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type="BOND",
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id, bond_type=BondType.TBILL, maturity_date=date(2026, 1, 1)
    )
    bond = crud.bond.create(db=db, obj_in=bond_in)
    bond2 = crud.bond.remove(db=db, id=bond.id)
    db.commit()
    bond3 = crud.bond.get(db=db, id=bond.id)
    assert bond3 is None
    assert bond2.id == bond.id

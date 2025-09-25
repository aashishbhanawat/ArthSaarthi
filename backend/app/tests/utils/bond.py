import random
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app import crud
from app.models.bond import Bond
from app.schemas.bond import BondCreate
from app.schemas.enums import BondType, PaymentFrequency


def create_random_bond(db: Session, *, asset_id: UUID) -> Bond:
    """
    Creates a random bond for a given asset.
    """
    bond_in = BondCreate(
        asset_id=asset_id,
        bond_type=random.choice(list(BondType)),
        face_value=Decimal(random.choice([100, 1000])),
        coupon_rate=Decimal(f"{random.uniform(5.0, 9.5):.2f}"),
        maturity_date=date.today() + timedelta(days=random.randint(365, 3650)),
        isin=None,
        payment_frequency=random.choice(list(PaymentFrequency)),
        first_payment_date=date.today() + timedelta(days=random.randint(30, 180)),
    )
    return crud.bond.create(db=db, obj_in=bond_in)

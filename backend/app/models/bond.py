import uuid

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class Bond(Base):
    __tablename__ = "bonds"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id = Column(GUID, ForeignKey("assets.id"), nullable=False, unique=True)
    bond_name = Column(String, nullable=False)
    isin = Column(String, nullable=True)
    face_value = Column(Numeric(precision=18, scale=2), nullable=False)
    coupon_rate = Column(Numeric(precision=5, scale=2), nullable=False)
    purchase_price = Column(Numeric(precision=18, scale=2), nullable=False)
    purchase_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    interest_payout_frequency = Column(
        Enum("ANNUALLY", "SEMI_ANNUALLY", name="interest_payout_frequency_enum"),
        nullable=False,
    )
    quantity = Column(Integer, nullable=False)

    asset = relationship("Asset", back_populates="bond_details")

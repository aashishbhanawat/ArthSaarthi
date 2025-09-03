import uuid

from sqlalchemy import Column, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class FixedDeposit(Base):
    __tablename__ = "fixed_deposits"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id = Column(GUID, ForeignKey("assets.id"), nullable=False, unique=True)
    institution_name = Column(String, nullable=False)
    account_number = Column(String, nullable=True)
    principal_amount = Column(Numeric(precision=18, scale=2), nullable=False)
    interest_rate = Column(Numeric(precision=5, scale=2), nullable=False)
    start_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    payout_type = Column(
        Enum("REINVESTMENT", "PAYOUT", name="payout_type_enum"), nullable=False
    )
    compounding_frequency = Column(
        Enum(
            "MONTHLY",
            "QUARTERLY",
            "HALF_YEARLY",
            "ANNUALLY",
            "AT_MATURITY",
            name="compounding_frequency_enum",
        ),
        nullable=False,
    )

    asset = relationship("Asset", back_populates="fixed_deposit_details")

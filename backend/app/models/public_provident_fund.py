import uuid

from sqlalchemy import Column, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class PublicProvidentFund(Base):
    __tablename__ = "public_provident_funds"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id = Column(GUID, ForeignKey("assets.id"), nullable=False, unique=True)
    institution_name = Column(String, nullable=False)
    account_number = Column(String, nullable=True)
    opening_date = Column(Date, nullable=False)
    current_balance = Column(Numeric(precision=18, scale=2), nullable=False)

    asset = relationship("Asset", back_populates="ppf_details")

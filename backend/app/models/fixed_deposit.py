import uuid
from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class FixedDeposit(Base):
    __tablename__ = "fixed_deposits"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    principal_amount = Column(Numeric(18, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    compounding_frequency = Column(String, nullable=False, server_default="Annually")
    interest_payout = Column(String, nullable=False, server_default="Cumulative")

    portfolio_id = Column(GUID, ForeignKey("portfolios.id"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)

    portfolio = relationship("Portfolio", back_populates="fixed_deposits")
    user = relationship("User", back_populates="fixed_deposits")

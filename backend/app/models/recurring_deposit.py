import uuid

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class RecurringDeposit(Base):
    __tablename__ = "recurring_deposits"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    account_number = Column(String, nullable=True)
    monthly_installment = Column(Numeric(18, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    tenure_months = Column(Integer, nullable=False)

    portfolio_id = Column(GUID, ForeignKey("portfolios.id"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)

    portfolio = relationship("Portfolio", back_populates="recurring_deposits")
    user = relationship("User", back_populates="recurring_deposits")

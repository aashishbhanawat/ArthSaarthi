import uuid
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    transaction_type = Column(String, nullable=False)  # e.g., 'BUY', 'SELL'
    quantity = Column(Numeric(18, 8), nullable=False)
    price_per_unit = Column(Numeric(18, 8), nullable=False)
    fees = Column(Numeric(18, 8), nullable=False, default=0)
    transaction_date = Column(DateTime, nullable=False)
    is_reinvested = Column(Boolean, default=False, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    portfolio_id = Column(GUID, ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(GUID, ForeignKey("assets.id"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)

    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")
    user = relationship("User", back_populates="transactions")

import uuid

from sqlalchemy import Column, String, ForeignKey, DateTime, Numeric, func
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_type = Column(String, nullable=False)  # e.g., 'BUY', 'SELL'
    quantity = Column(Numeric(18, 8), nullable=False)
    price_per_unit = Column(Numeric(18, 8), nullable=False)
    fees = Column(Numeric(18, 8), nullable=False, default=0)
    transaction_date = Column(DateTime(timezone=True), nullable=False)

    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
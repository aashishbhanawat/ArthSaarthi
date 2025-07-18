from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String, nullable=False)  # e.g., 'BUY', 'SELL'
    quantity = Column(Numeric(18, 8), nullable=False)
    price_per_unit = Column(Numeric(18, 8), nullable=False)
    fees = Column(Numeric(18, 8), nullable=False, default=0)
    transaction_date = Column(DateTime(timezone=True), nullable=False)

    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
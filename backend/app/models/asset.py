from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    ticker_symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)  # e.g., 'STOCK', 'ETF'
    currency = Column(String, nullable=False)  # e.g., 'USD', 'INR'

    transactions = relationship("Transaction", back_populates="asset")

    __table_args__ = (
        UniqueConstraint('ticker_symbol', name='uq_ticker_symbol'),
    )
import uuid

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class Asset(Base):
    __tablename__ = "assets"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    ticker_symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)  # e.g., 'STOCK', 'ETF'
    currency = Column(String, nullable=False)  # e.g., 'USD', 'INR'
    exchange = Column(String, nullable=False, server_default="N/A")
    isin = Column(String, unique=True, index=True, nullable=True)
    portfolio_id = Column(GUID, ForeignKey("portfolios.id"), nullable=True)

    portfolio = relationship("Portfolio", back_populates="assets")
    transactions = relationship("Transaction", back_populates="asset")
    aliases = relationship(
        "AssetAlias", back_populates="asset", cascade="all, delete-orphan"
    )
    watchlist_items = relationship("WatchlistItem", back_populates="asset")

    # Relationships to details tables
    fixed_deposit_details = relationship(
        "FixedDeposit",
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
    )
    ppf_details = relationship(
        "PublicProvidentFund",
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
    )
    bond_details = relationship(
        "Bond", back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("ticker_symbol", name="uq_ticker_symbol"),)

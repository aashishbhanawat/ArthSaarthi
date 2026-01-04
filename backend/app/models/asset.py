import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.custom_types import GUID

from .asset_alias import AssetAlias
from .watchlist import WatchlistItem

if TYPE_CHECKING:
    from .bond import Bond  # noqa: F401
    from .transaction import Transaction  # noqa: F401


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    ticker_symbol: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    asset_type: Mapped[str] = mapped_column(String)
    currency: Mapped[str] = mapped_column(String)
    exchange: Mapped[str] = mapped_column(String, server_default="N/A")
    isin: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    # For FDs, RDs, etc.
    account_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # For PPF accounts
    opening_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # For diversification analysis (FR6.4)
    sector: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    market_cap: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )  # BigInteger for large market caps
    # Investment style classification (Value/Growth/Blend)
    investment_style: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="asset")
    aliases: Mapped[List[AssetAlias]] = relationship(
        "AssetAlias", back_populates="asset", cascade="all, delete-orphan"
    )
    watchlist_items: Mapped[List[WatchlistItem]] = relationship(
        back_populates="asset")

    # Add the relationship to the Bond model
    bond: Mapped["Bond"] = relationship(
        "Bond", back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("ticker_symbol", name="uq_ticker_symbol"),)

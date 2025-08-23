import uuid

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="watchlists")
    items = relationship(
        "WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    watchlist_id = Column(GUID, ForeignKey("watchlists.id"), nullable=False)
    asset_id = Column(GUID, ForeignKey("assets.id"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)

    watchlist = relationship("Watchlist", back_populates="items")
    asset = relationship("Asset")

    __table_args__ = (
        UniqueConstraint("watchlist_id", "asset_id", name="uq_watchlist_asset"),
    )

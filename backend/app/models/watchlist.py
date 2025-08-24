import uuid

from sqlalchemy import (Column, DateTime, ForeignKey, String, func,
                        UniqueConstraint)
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime, server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="watchlists")
    items = relationship(
        "WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "asset_id", name="uq_watchlist_asset"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    watchlist_id = Column(GUID, ForeignKey("watchlists.id"), nullable=False)
    asset_id = Column(GUID, ForeignKey("assets.id"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False) # As per spec

    watchlist = relationship("Watchlist", back_populates="items")
    asset = relationship("Asset", back_populates="watchlist_items")
    user = relationship("User", back_populates="watchlist_items")

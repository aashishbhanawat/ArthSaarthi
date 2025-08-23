import uuid

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db.base_class import Base


class Watchlist(Base):
    __tablename__ = "watchlists"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="watchlists")
    items = relationship(
        "WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan"
    )
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="_user_watchlist_name_uc"),
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watchlist_id = Column(
        UUID(as_uuid=True), ForeignKey("watchlists.id"), nullable=False
    )
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    watchlist = relationship("Watchlist", back_populates="items")
    asset = relationship("Asset")
    __table_args__ = (
        UniqueConstraint("watchlist_id", "asset_id", name="_watchlist_asset_uc"),
    )

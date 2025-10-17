import uuid

from sqlalchemy import Boolean, Column, DateTime, String, func
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID, EncryptedString

# The following imports are needed for SQLAlchemy to correctly resolve relationships
# from string-based definitions, preventing circular import errors at runtime.
from . import fixed_deposit, recurring_deposit  # noqa: F401


class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    full_name = Column(EncryptedString, index=True, nullable=True)
    email = Column(EncryptedString, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean(), default=False, nullable=False)
    is_active = Column(Boolean(), default=True)
    created_at = Column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    portfolios = relationship(
        "Portfolio", back_populates="user", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    import_sessions = relationship(
        "ImportSession", back_populates="user", cascade="all, delete-orphan"
    )
    watchlists = relationship(
        "Watchlist", back_populates="user", cascade="all, delete-orphan"
    )
    watchlist_items = relationship(
        "WatchlistItem", back_populates="user", cascade="all, delete-orphan"
    )
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    fixed_deposits = relationship(
        "FixedDeposit", back_populates="user", cascade="all, delete-orphan"
    )
    recurring_deposits = relationship(
        "RecurringDeposit", back_populates="user", cascade="all, delete-orphan"
    )

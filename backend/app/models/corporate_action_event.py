import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.custom_types import GUID

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.portfolio import Portfolio
    from app.models.transaction import Transaction
    from app.models.user import User


class CorporateActionEvent(Base):
    __tablename__ = "corporate_action_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    units: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="NEW"
    )  # NEW, READ, DISMISSED
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")
    portfolio: Mapped["Portfolio"] = relationship("Portfolio")
    asset: Mapped["Asset"] = relationship("Asset")
    transaction: Mapped[Optional["Transaction"]] = relationship("Transaction")

    __table_args__ = (
        Index("ix_corporate_action_events_user_status", "user_id", "status"),
    )

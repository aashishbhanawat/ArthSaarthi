import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base_class import Base


class CapitalLossLedger(Base):
    __tablename__ = "capital_loss_ledgers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    financial_year = Column(String(7), nullable=False)  # e.g. "2023-24"
    assessment_year = Column(String(7), nullable=False)  # e.g. "2024-25"
    stcl_amount = Column(Numeric(14, 2), nullable=False, default=0.0)
    ltcl_amount = Column(Numeric(14, 2), nullable=False, default=0.0)
    is_itr_filed_on_time = Column(Boolean, nullable=False, default=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

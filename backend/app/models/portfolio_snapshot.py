import uuid

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class DailyPortfolioSnapshot(Base):
    __tablename__ = "daily_portfolio_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True
    )
    snapshot_date = Column(Date, nullable=False, index=True)

    # Portfolio breakdown (up to 18 digits, 2 decimal places)
    total_value = Column(Numeric(18, 2), nullable=False)
    equity_value = Column(Numeric(18, 2), nullable=False, default=0)
    mf_value = Column(Numeric(18, 2), nullable=False, default=0)
    bond_value = Column(Numeric(18, 2), nullable=False, default=0)
    fd_value = Column(Numeric(18, 2), nullable=False, default=0)

    # Optional JSON payload holding point-in-time state of the portfolio
    holdings_snapshot = Column(JSON, nullable=True)

    # Standard audit timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


    # Automatically set back-population relationship
    portfolio = relationship("Portfolio", back_populates="snapshots")

    __table_args__ = (
        UniqueConstraint(
            'portfolio_id', 'snapshot_date', name='uq_portfolio_date_snapshot'
        ),
    )

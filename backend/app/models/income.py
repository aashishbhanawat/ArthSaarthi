import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID, EncryptedString


class IncomeSource(Base):
    __tablename__ = "income_sources"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    name = Column(EncryptedString, nullable=False)
    # SALARY, FREELANCE, RENTAL, DIVIDEND, INTEREST, BUSINESS, OTHER
    category = Column(String, nullable=False)
    payer_name = Column(EncryptedString, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="income_sources")
    entries = relationship(
        "IncomeEntry",
        back_populates="source",
        cascade="all, delete-orphan",
    )


class IncomeEntry(Base):
    __tablename__ = "income_entries"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    source_id = Column(GUID, ForeignKey("income_sources.id"), nullable=False)
    financial_year = Column(String, nullable=False, index=True)  # e.g., "2025-2026"
    entry_date = Column(Date, nullable=False)
    gross_amount = Column(EncryptedString, nullable=False)
    tds_amount = Column(EncryptedString, nullable=False, default="0.00")
    net_amount = Column(EncryptedString, nullable=False)
    notes = Column(EncryptedString, nullable=True)

    # FR16.5: Optional Salary Breakdown & Section 10(13A) HRA Exemption fields
    basic_amount = Column(EncryptedString, nullable=True)
    hra_amount = Column(EncryptedString, nullable=True)
    da_amount = Column(EncryptedString, nullable=True)
    special_allowance_amount = Column(EncryptedString, nullable=True)
    other_allowances_amount = Column(EncryptedString, nullable=True)
    other_benefits_amount = Column(EncryptedString, nullable=True)
    rent_paid = Column(EncryptedString, nullable=True)
    is_metro = Column(Boolean, default=False, nullable=True)
    hra_exemption = Column(EncryptedString, nullable=True, default="0.00")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User")
    source = relationship("IncomeSource", back_populates="entries")


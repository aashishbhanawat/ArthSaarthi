import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID, EncryptedString


class TaxDeduction(Base):
    __tablename__ = "tax_deductions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    financial_year = Column(String, nullable=False, index=True)
    section = Column(String, nullable=False, index=True)
    title = Column(EncryptedString, nullable=False)
    amount = Column(EncryptedString, nullable=False)
    deduction_date = Column(Date, nullable=False)
    proof_notes = Column(EncryptedString, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="tax_deductions")

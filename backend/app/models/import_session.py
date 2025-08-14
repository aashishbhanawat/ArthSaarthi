import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class ImportSession(Base):
    __tablename__ = "import_sessions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(GUID, ForeignKey("portfolios.id"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    source = Column(String, nullable=False)
    parsed_file_path = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    status = Column(String, nullable=False, default="UPLOADED")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="import_sessions")
    portfolio = relationship("Portfolio", back_populates="import_sessions")
    parsed_transactions = relationship(
        "ParsedTransaction", back_populates="session", cascade="all, delete-orphan"
    )

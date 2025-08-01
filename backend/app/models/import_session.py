from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ImportSession(Base):
    __tablename__ = "import_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Path to the temporarily stored file
    parsed_file_path = Column(String, nullable=True) # Path to the parsed data file
    status = Column(String, nullable=False, default="UPLOADED")  # e.g., 'UPLOADED', 'PARSED', 'REVIEW', 'COMPLETED', 'FAILED'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="import_sessions")

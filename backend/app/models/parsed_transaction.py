import uuid

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import UUID
from app.db.utils import get_db_type

if get_db_type() == "postgresql":
    from sqlalchemy.dialects.postgresql import JSONB
else:
    JSONB = JSON


class ParsedTransaction(Base):
    __tablename__ = "parsed_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("import_sessions.id"), nullable=False
    )
    row_number = Column(Integer, nullable=False)
    data = Column(JSONB, nullable=False)
    is_selected = Column(Boolean, default=True, nullable=False)

    session = relationship("ImportSession", back_populates="parsed_transactions")

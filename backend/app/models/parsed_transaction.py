import uuid

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class ParsedTransaction(Base):
    __tablename__ = "parsed_transactions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("import_sessions.id"), nullable=False)
    row_number = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)
    is_selected = Column(Boolean, default=True, nullable=False)

    session = relationship("ImportSession", back_populates="parsed_transactions")

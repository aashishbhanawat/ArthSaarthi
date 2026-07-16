import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID, EncryptedString


class UserRiskProfile(Base):
    __tablename__ = "user_risk_profiles"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), unique=True, nullable=False)
    answers = Column(EncryptedString, nullable=False)
    score = Column(Integer, nullable=True)
    risk_category = Column(String, nullable=True)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", backref="risk_profile")

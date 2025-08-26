import uuid
from sqlalchemy import Column, String, Numeric, Date, ForeignKey, CheckConstraint, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.db.custom_types import GUID


class Goal(Base):
    __tablename__ = "goals"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    target_amount = Column(Numeric, nullable=False)
    target_date = Column(Date, nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="goals")
    links = relationship("GoalLink", back_populates="goal", cascade="all, delete-orphan")

class GoalLink(Base):
    __tablename__ = "goal_links"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    goal_id = Column(GUID, ForeignKey("goals.id"), nullable=False)
    portfolio_id = Column(GUID, ForeignKey("portfolios.id"), nullable=True)
    asset_id = Column(GUID, ForeignKey("assets.id"), nullable=True)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)

    goal = relationship("Goal", back_populates="links")
    portfolio = relationship("Portfolio")
    asset = relationship("Asset")
    user = relationship("User")

    __table_args__ = (
        CheckConstraint(
            '(portfolio_id IS NOT NULL AND asset_id IS NULL) OR (portfolio_id IS NULL AND asset_id IS NOT NULL)',
            name='check_goal_link_target'
        ),
    )

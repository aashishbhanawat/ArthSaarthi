import uuid
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# Schemas for Goal
class GoalBase(BaseModel):
    name: str
    target_amount: float
    target_date: date


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = None
    target_date: Optional[date] = None


class Goal(GoalBase):
    id: uuid.UUID
    user_id: uuid.UUID
    links: List["GoalLink"] = []
    model_config = ConfigDict(from_attributes=True)


class GoalWithAnalytics(Goal):
    current_amount: float
    progress: float


# Schemas for GoalLink
class GoalLinkBase(BaseModel):
    goal_id: uuid.UUID
    portfolio_id: Optional[uuid.UUID] = None
    asset_id: Optional[uuid.UUID] = None


class GoalLinkCreate(GoalLinkBase):
    pass


class GoalLinkUpdate(BaseModel):
    # For now, a link is immutable, so no fields are updatable.
    # This can be expanded later if needed.
    pass


class GoalLink(GoalLinkBase):
    id: uuid.UUID
    user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

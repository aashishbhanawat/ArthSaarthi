import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# Shared properties for GoalLink
class GoalLinkBase(BaseModel):
    portfolio_id: Optional[uuid.UUID] = None
    asset_id: Optional[uuid.UUID] = None


# Properties to receive on GoalLink creation
class GoalLinkCreate(GoalLinkBase):
    goal_id: uuid.UUID


# Properties to receive on GoalLink update
class GoalLinkUpdate(BaseModel):
    pass  # Goal links are not updatable, they are created and deleted


# Properties to return to client for GoalLink
class GoalLink(GoalLinkBase):
    id: uuid.UUID
    goal_id: uuid.UUID
    user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# Shared properties for Goal
class GoalBase(BaseModel):
    name: str
    target_amount: float
    target_date: date


# Properties to receive on Goal creation
class GoalCreate(GoalBase):
    pass


# Properties to receive on Goal update
class GoalUpdate(GoalBase):
    name: Optional[str] = None
    target_amount: Optional[float] = None
    target_date: Optional[date] = None


# Properties to return to client for Goal
class Goal(GoalBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    links: list[GoalLink] = []
    model_config = ConfigDict(from_attributes=True)

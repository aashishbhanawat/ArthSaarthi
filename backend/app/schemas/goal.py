import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from .asset import Asset
from .portfolio import Portfolio


# GoalLink Schemas
class GoalLinkBase(BaseModel):
    portfolio_id: Optional[uuid.UUID] = None
    asset_id: Optional[uuid.UUID] = None


class GoalLinkCreateIn(GoalLinkBase):
    pass

class GoalLinkCreate(GoalLinkBase):
    goal_id: uuid.UUID


class GoalLinkUpdate(BaseModel):
    pass


class GoalLink(GoalLinkBase):
    id: uuid.UUID
    goal_id: uuid.UUID
    user_id: uuid.UUID
    portfolio: Optional[Portfolio] = None
    asset: Optional[Asset] = None
    model_config = ConfigDict(from_attributes=True)


# Goal Schemas
class GoalBase(BaseModel):
    name: str
    target_amount: Decimal
    target_date: date


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[Decimal] = None
    target_date: Optional[date] = None


class Goal(GoalBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    links: List[GoalLink] = []
    model_config = ConfigDict(from_attributes=True)


class GoalWithAnalytics(Goal):
    current_value: Decimal
    progress: float

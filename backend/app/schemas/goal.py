import uuid
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from pydantic.version import VERSION

try:
    if VERSION.startswith("2."):
        from pydantic import ConfigDict
    else:
        raise ImportError
except ImportError:
    ConfigDict = None


# Schemas for Goal
class GoalBase(BaseModel):
    name: str
    target_amount: float
    target_date: date
    expected_return: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = None
    target_date: Optional[date] = None
    expected_return: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class Goal(GoalBase):
    id: uuid.UUID
    user_id: uuid.UUID
    links: List["GoalLink"] = []
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class GoalProjectionPoint(BaseModel):
    date: str
    projected_value: float
    target_value: float


class GoalWithAnalytics(Goal):
    current_amount: float
    progress: float
    required_sip: float = 0.0
    calculated_return_rate: float = 10.0
    linked_assets_xirr: float = 0.0
    projected_future_value: float = 0.0
    status: str = "Off Track"
    projection_chart_data: List[GoalProjectionPoint] = []


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


# Add minimal schemas for nested objects to avoid circular imports
# and expose necessary fields.
class AssetInGoalLink(BaseModel):
    id: uuid.UUID
    name: str
    ticker_symbol: str
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

class PortfolioInGoalLink(BaseModel):
    id: uuid.UUID
    name: str
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class GoalLink(GoalLinkBase):
    id: uuid.UUID
    user_id: uuid.UUID
    asset: Optional[AssetInGoalLink] = None
    portfolio: Optional[PortfolioInGoalLink] = None
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

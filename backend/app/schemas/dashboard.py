from datetime import date
from decimal import Decimal
from typing import List

from pydantic import BaseModel
from pydantic.version import VERSION

try:
    if VERSION.startswith("2."):
        from pydantic import ConfigDict
    else:
        raise ImportError
except ImportError:
    ConfigDict = None


# For Portfolio History Endpoint
class PortfolioHistoryPoint(BaseModel):
    date: date
    value: Decimal
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class PortfolioHistoryResponse(BaseModel):
    history: List[PortfolioHistoryPoint]
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


# For Asset Allocation Endpoint
class AssetAllocation(BaseModel):
    ticker: str
    value: Decimal
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class AssetAllocationResponse(BaseModel):
    allocation: List[AssetAllocation]
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class TopMover(BaseModel):
    ticker_symbol: str
    currency: str
    name: str
    current_price: Decimal
    daily_change: Decimal
    daily_change_percentage: float


class DashboardSummary(BaseModel):
    total_value: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
    top_movers: List[TopMover]
    asset_allocation: List[AssetAllocation]
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

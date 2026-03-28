from datetime import date
from decimal import Decimal
from typing import List

from pydantic import BaseModel


# For Portfolio History Endpoint
class PortfolioHistoryPoint(BaseModel):
    date: date
    value: Decimal
    class Config:
        from_attributes = True
        orm_mode = True


class PortfolioHistoryResponse(BaseModel):
    history: List[PortfolioHistoryPoint]
    class Config:
        from_attributes = True
        orm_mode = True


# For Asset Allocation Endpoint
class AssetAllocation(BaseModel):
    ticker: str
    value: Decimal
    class Config:
        from_attributes = True
        orm_mode = True


class AssetAllocationResponse(BaseModel):
    allocation: List[AssetAllocation]
    class Config:
        from_attributes = True
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
    class Config:
        from_attributes = True
        orm_mode = True

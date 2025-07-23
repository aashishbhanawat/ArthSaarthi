from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import List
from datetime import date


class DashboardAsset(BaseModel):
    ticker_symbol: str
    current_price: Decimal
    price_change_24h: Decimal
    price_change_percentage_24h: Decimal
    model_config = ConfigDict(from_attributes=True)


# For Portfolio History Endpoint
class PortfolioHistoryPoint(BaseModel):
    date: date
    value: Decimal
    model_config = ConfigDict(from_attributes=True)


class PortfolioHistoryResponse(BaseModel):
    history: List[PortfolioHistoryPoint]
    model_config = ConfigDict(from_attributes=True)


# For Asset Allocation Endpoint
class AssetAllocation(BaseModel):
    ticker: str
    value: Decimal
    model_config = ConfigDict(from_attributes=True)


class AssetAllocationResponse(BaseModel):
    allocation: List[AssetAllocation]
    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    total_value: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
    top_movers: List[DashboardAsset]
    asset_allocation: List[AssetAllocation]
    model_config = ConfigDict(from_attributes=True)
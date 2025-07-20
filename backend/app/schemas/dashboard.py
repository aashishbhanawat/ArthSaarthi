from pydantic import BaseModel
from decimal import Decimal
from typing import List


class DashboardAsset(BaseModel):
    ticker_symbol: str
    current_price: Decimal
    price_change_24h: Decimal
    price_change_percentage_24h: Decimal

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_value: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
    top_movers: List[DashboardAsset]

    class Config:
        from_attributes = True
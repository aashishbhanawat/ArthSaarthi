import uuid
from decimal import Decimal
from typing import List

from pydantic import BaseModel


class Holding(BaseModel):
    asset_id: uuid.UUID
    ticker_symbol: str
    asset_name: str
    asset_type: str
    quantity: Decimal
    average_buy_price: Decimal
    total_invested_amount: Decimal
    current_price: Decimal
    current_value: Decimal
    days_pnl: Decimal
    days_pnl_percentage: float
    unrealized_pnl: Decimal
    unrealized_pnl_percentage: float

    class Config:
        from_attributes = True


class HoldingsResponse(BaseModel):
    holdings: List[Holding]


class PortfolioSummary(BaseModel):
    total_value: Decimal
    total_invested_amount: Decimal
    days_pnl: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal

    class Config:
        from_attributes = True

import uuid
from decimal import Decimal
from typing import List

from pydantic import BaseModel


class Holding(BaseModel):
    asset_id: uuid.UUID
    asset_name: str
    asset_type: str
    current_value: Decimal
    total_invested_amount: Decimal

    ticker_symbol: str | None = None
    quantity: Decimal | None = None
    average_buy_price: Decimal | None = None
    current_price: Decimal | None = None
    days_pnl: Decimal | None = None
    days_pnl_percentage: float | None = None
    unrealized_pnl: Decimal | None = None
    unrealized_pnl_percentage: float | None = None

    # Optional fields for Fixed Deposits
    institution_name: str | None = None
    interest_rate: Decimal | None = None
    maturity_date: str | None = None

    # Optional fields for Bonds
    coupon_rate: Decimal | None = None

    # Optional fields for PPF
    opening_date: str | None = None

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

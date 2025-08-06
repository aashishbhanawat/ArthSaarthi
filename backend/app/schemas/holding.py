from pydantic import BaseModel, ConfigDict
from decimal import Decimal
import uuid
from typing import List


class Holding(BaseModel):
    """
    Represents a single consolidated holding in a portfolio.
    """
    asset_id: uuid.UUID
    ticker_symbol: str
    asset_name: str
    quantity: Decimal
    average_buy_price: Decimal
    total_invested_amount: Decimal
    current_price: Decimal
    current_value: Decimal
    days_pnl: Decimal
    days_pnl_percentage: float
    unrealized_pnl: Decimal
    unrealized_pnl_percentage: float

    model_config = ConfigDict(from_attributes=True)


class HoldingsResponse(BaseModel):
    """
    Response model for the list of portfolio holdings.
    """
    holdings: List[Holding]


class PortfolioSummary(BaseModel):
    """
    Response model for the portfolio summary metrics.
    """
    total_value: Decimal
    total_invested_amount: Decimal
    days_pnl: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
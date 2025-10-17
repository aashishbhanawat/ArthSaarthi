import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, model_validator

from .bond import Bond as BondSchema


class Holding(BaseModel):
    asset_id: uuid.UUID
    ticker_symbol: str
    asset_name: str
    asset_type: str
    group: str
    quantity: Decimal
    average_buy_price: Decimal
    total_invested_amount: Decimal
    current_price: Decimal
    current_value: Decimal
    days_pnl: Decimal
    days_pnl_percentage: float
    unrealized_pnl: Decimal
    unrealized_pnl_percentage: float
    realized_pnl: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    maturity_date: Optional[date] = None
    account_number: Optional[str] = None
    isin: Optional[str] = None
    opening_date: Optional[date] = None
    bond: Optional[BondSchema] = None

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def apply_fallbacks_and_enrich(self) -> "Holding":
        if self.bond:
            self.interest_rate = self.bond.coupon_rate
            self.maturity_date = self.bond.maturity_date
            if not self.isin:
                self.isin = self.bond.isin

        # For certain asset types where a live price might not be available (e.g.,
        # unlisted bonds, RDs), fall back to using the average buy price to avoid
        # showing a 100% loss. This should NOT apply to stocks.
        if (
            self.asset_type in ["BOND", "RECURRING_DEPOSIT"]
            and (self.current_price is None or self.current_price == 0)
            and self.average_buy_price > 0
        ):
            self.current_price = self.average_buy_price
            self.current_value = self.quantity * self.average_buy_price
            self.unrealized_pnl = Decimal("0.0")
            self.unrealized_pnl_percentage = 0.0
        else:
            # For market-traded assets with a valid current price, ensure P&L is
            # calculated.
            # Exclude assets like PPF which have their own specialized P&L calculation.
            if self.asset_type not in ["PPF"]:
                self.unrealized_pnl = self.current_value - self.total_invested_amount
                if self.total_invested_amount > 0:
                    self.unrealized_pnl_percentage = float(
                        self.unrealized_pnl / self.total_invested_amount)

        return self


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

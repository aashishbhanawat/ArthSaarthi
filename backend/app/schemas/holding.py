import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, root_validator

from pydantic.version import VERSION

try:
    if VERSION.startswith("2."):
        from pydantic import ConfigDict
    else:
        raise ImportError
    def model_validator(pre=False, mode="after"):
        return root_validator(pre=pre, skip_on_failure=True)
except (ImportError, TypeError):
    ConfigDict = None
    def model_validator(pre=False, mode="after"):
        return root_validator(pre=pre)

from .bond import Bond as BondSchema


class Holding(BaseModel):
    asset_id: uuid.UUID
    ticker_symbol: str
    asset_name: str
    asset_type: str
    currency: str
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
    investment_style: Optional[str] = None  # Value, Growth, Blend
    bond: Optional[BondSchema] = None

    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


    @model_validator(pre=False)
    @classmethod
    def apply_fallbacks_and_enrich(cls, values: dict) -> dict:
        bond = values.get("bond")
        if bond:
            # Depending on pydantic version, bond might be a dict or a model instance
            coupon_rate = bond.coupon_rate if hasattr(bond, "coupon_rate") else bond.get("coupon_rate")
            maturity_date = bond.maturity_date if hasattr(bond, "maturity_date") else bond.get("maturity_date")
            isin = bond.isin if hasattr(bond, "isin") else bond.get("isin")
            
            values["interest_rate"] = coupon_rate
            values["maturity_date"] = maturity_date
            if not values.get("isin"):
                values["isin"] = isin

        # For certain asset types where a live price might not be available (e.g.,
        # unlisted bonds, RDs), fall back to using the average buy price to avoid
        # showing a 100% loss. This should NOT apply to stocks.
        if (
            values.get("asset_type") == "BOND"
            and values.get("current_price") == 0
        ):
            avg = values.get("average_buy_price")
            values["current_price"] = avg
            qty = values.get("quantity")
            if qty is not None and avg is not None:
                values["current_value"] = qty * avg

        return values


class HoldingsResponse(BaseModel):
    holdings: List[Holding]


class PortfolioSummary(BaseModel):
    total_value: Decimal
    total_invested_amount: Decimal
    days_pnl: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal

    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True



class PortfolioHoldingsAndSummary(BaseModel):
    summary: PortfolioSummary
    holdings: List[Holding]
    
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


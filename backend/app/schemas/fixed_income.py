import uuid
from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class PayoutType(str, Enum):
    REINVESTMENT = "REINVESTMENT"
    PAYOUT = "PAYOUT"


class CompoundingFrequency(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    ANNUALLY = "ANNUALLY"
    AT_MATURITY = "AT_MATURITY"


class FixedDepositBase(BaseModel):
    institution_name: str
    account_number: str | None = None
    principal_amount: float = Field(..., gt=0)
    interest_rate: float = Field(..., gt=0)
    start_date: date
    maturity_date: date
    payout_type: PayoutType
    compounding_frequency: CompoundingFrequency


class FixedDepositCreate(FixedDepositBase):
    pass


class FixedDepositUpdate(FixedDepositBase):
    pass


class FixedDeposit(FixedDepositBase):
    id: uuid.UUID
    asset_id: uuid.UUID

    class Config:
        from_attributes = True


# PPF Schemas
class PublicProvidentFundBase(BaseModel):
    institution_name: str
    account_number: str | None = None
    opening_date: date
    current_balance: float = Field(..., ge=0)


class PublicProvidentFundCreate(PublicProvidentFundBase):
    pass


class PublicProvidentFundUpdate(PublicProvidentFundBase):
    pass


class PublicProvidentFund(PublicProvidentFundBase):
    id: uuid.UUID
    asset_id: uuid.UUID

    class Config:
        from_attributes = True


# Bond Schemas
class InterestPayoutFrequency(str, Enum):
    ANNUALLY = "ANNUALLY"
    SEMI_ANNUALLY = "SEMI_ANNUALLY"


class BondBase(BaseModel):
    bond_name: str
    isin: str | None = None
    face_value: float = Field(..., gt=0)
    coupon_rate: float = Field(..., ge=0)
    purchase_price: float = Field(..., ge=0)
    purchase_date: date
    maturity_date: date
    interest_payout_frequency: InterestPayoutFrequency
    quantity: int = Field(..., gt=0)


class BondCreate(BondBase):
    pass


class BondUpdate(BondBase):
    pass


class Bond(BondBase):
    id: uuid.UUID
    asset_id: uuid.UUID

    class Config:
        from_attributes = True

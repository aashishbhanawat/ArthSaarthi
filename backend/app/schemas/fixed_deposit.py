import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class FixedDepositBase(BaseModel):
    name: str
    account_number: str | None = None
    principal_amount: Decimal
    interest_rate: Decimal
    start_date: date
    maturity_date: date
    compounding_frequency: str
    interest_payout: str


class FixedDepositCreate(FixedDepositBase):
    pass


class FixedDepositUpdate(FixedDepositBase):
    pass


class FixedDeposit(FixedDepositBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    user_id: uuid.UUID

    class Config:
        from_attributes = True


class FixedDepositDetails(FixedDeposit):
    maturity_value: Decimal

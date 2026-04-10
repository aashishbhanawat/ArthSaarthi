import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, root_validator


class FixedDepositBase(BaseModel):
    name: str
    account_number: str | None = None
    principal_amount: Decimal
    interest_rate: Decimal
    start_date: date
    maturity_date: date
    compounding_frequency: str
    interest_payout: str

    @root_validator(pre=False, skip_on_failure=True)
    @classmethod
    def check_dates(cls, values: dict) -> dict:
        start_date = values.get("start_date")
        maturity_date = values.get("maturity_date")
        if start_date and start_date > date.today():
            raise ValueError("Start date cannot be in the future")
        if start_date and maturity_date and maturity_date <= start_date:
            raise ValueError("Maturity date must be after start date")
        return values


class FixedDepositCreate(FixedDepositBase):
    portfolio_id: uuid.UUID


class FixedDepositUpdate(BaseModel):
    name: str | None = None
    account_number: str | None = None
    principal_amount: Decimal | None = None
    interest_rate: Decimal | None = None
    start_date: date | None = None
    maturity_date: date | None = None
    compounding_frequency: str | None = None
    interest_payout: str | None = None


class FixedDeposit(FixedDepositBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    user_id: uuid.UUID

    class Config:
        from_attributes = True
        from_attributes = True


class FixedDepositDetails(FixedDeposit):
    maturity_value: Decimal

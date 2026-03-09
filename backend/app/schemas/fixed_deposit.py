import uuid
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, model_validator


class FixedDepositBase(BaseModel):
    name: str
    account_number: str | None = None
    principal_amount: Decimal
    interest_rate: Decimal
    start_date: date
    maturity_date: date
    compounding_frequency: str
    interest_payout: str

    @model_validator(mode="after")
    def check_dates(self) -> "FixedDepositBase":
        if self.start_date > date.today():
            raise ValueError("Start date cannot be in the future")
        if self.maturity_date <= self.start_date:
            raise ValueError("Maturity date must be after start date")
        return self


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


class FixedDepositDetails(FixedDeposit):
    maturity_value: Decimal

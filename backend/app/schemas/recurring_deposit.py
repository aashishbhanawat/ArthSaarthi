import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class RecurringDepositBase(BaseModel):
    name: str
    monthly_installment: Decimal
    interest_rate: Decimal
    start_date: date
    tenure_months: int


class RecurringDepositCreate(RecurringDepositBase):
    pass


class RecurringDepositUpdate(BaseModel):
    name: Optional[str] = None
    monthly_installment: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    start_date: Optional[date] = None
    tenure_months: Optional[int] = None


class RecurringDeposit(RecurringDepositBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    user_id: uuid.UUID

    class Config:
        from_attributes = True


class RecurringDepositDetails(RecurringDeposit):
    maturity_value: Decimal


class RecurringDepositAnalytics(BaseModel):
    unrealized_xirr: float

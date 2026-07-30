import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from pydantic.version import VERSION

try:
    if VERSION.startswith("2."):
        from pydantic import ConfigDict
    else:
        ConfigDict = None
except ImportError:
    ConfigDict = None


class RecurringDepositBase(BaseModel):
    name: str
    account_number: Optional[str] = None
    monthly_installment: Decimal
    interest_rate: Decimal
    start_date: date
    tenure_months: int


class RecurringDepositCreate(RecurringDepositBase):
    portfolio_id: uuid.UUID


class RecurringDepositUpdate(BaseModel):
    name: Optional[str] = None
    account_number: Optional[str] = None
    monthly_installment: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    start_date: Optional[date] = None
    tenure_months: Optional[int] = None




class RecurringDeposit(RecurringDepositBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    user_id: uuid.UUID

    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True



class RecurringDepositDetails(RecurringDeposit):
    maturity_value: Decimal


class RecurringDepositAnalytics(BaseModel):
    unrealized_xirr: float

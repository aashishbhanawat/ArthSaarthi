import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class HistoricalInterestRateBase(BaseModel):
    scheme_name: str
    start_date: date
    end_date: date
    rate: Decimal


class HistoricalInterestRateCreate(HistoricalInterestRateBase):
    pass


class HistoricalInterestRateUpdate(BaseModel):
    scheme_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rate: Optional[Decimal] = None


class HistoricalInterestRateInDBBase(HistoricalInterestRateBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class HistoricalInterestRate(HistoricalInterestRateInDBBase):
    pass

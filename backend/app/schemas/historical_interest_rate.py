import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class HistoricalInterestRateBase(BaseModel):
    scheme_name: str = Field(..., example="PPF")
    start_date: date = Field(..., example="2023-04-01")
    end_date: Optional[date] = Field(None, example="2024-03-31")
    rate: Decimal = Field(..., ge=0, le=100, example=7.100)


class HistoricalInterestRateCreate(HistoricalInterestRateBase):
    pass


class HistoricalInterestRateUpdate(HistoricalInterestRateBase):
    scheme_name: Optional[str] = None
    start_date: Optional[date] = None
    rate: Optional[Decimal] = None


class HistoricalInterestRateInDBBase(HistoricalInterestRateBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class HistoricalInterestRate(HistoricalInterestRateInDBBase):
    pass

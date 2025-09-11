import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class HistoricalInterestRateBase(BaseModel):
    scheme_name: str
    start_date: date
    end_date: date
    rate: Decimal


class HistoricalInterestRateCreate(HistoricalInterestRateBase):
    pass


class HistoricalInterestRateUpdate(BaseModel):
    pass


class HistoricalInterestRate(HistoricalInterestRateBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

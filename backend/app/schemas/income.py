import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator
from pydantic.version import VERSION

try:
    if VERSION.startswith("2."):
        from pydantic import ConfigDict
    else:
        raise ImportError
except ImportError:
    ConfigDict = None


# IncomeSource Schemas
class IncomeSourceBase(BaseModel):
    name: str
    category: str  # SALARY, FREELANCE, RENTAL, DIVIDEND, INTEREST, BUSINESS, OTHER
    payer_name: Optional[str] = None


class IncomeSourceCreate(IncomeSourceBase):
    pass


class IncomeSourceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    payer_name: Optional[str] = None


class IncomeSource(IncomeSourceBase):
    id: uuid.UUID
    user_id: uuid.UUID

    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


# IncomeEntry Schemas
class IncomeEntryBase(BaseModel):
    source_id: uuid.UUID
    financial_year: str
    entry_date: date
    gross_amount: Decimal = Field(gt=0, description="Gross income amount")
    tds_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="TDS deducted at source")
    notes: Optional[str] = None

    @validator("tds_amount")
    def tds_must_not_exceed_gross(cls, v, values):
        if "gross_amount" in values and values["gross_amount"] is not None:
            if v > values["gross_amount"]:
                raise ValueError("TDS amount cannot exceed gross income amount")
        return v


class IncomeEntryCreate(IncomeEntryBase):
    pass


class IncomeEntryUpdate(BaseModel):
    source_id: Optional[uuid.UUID] = None
    financial_year: Optional[str] = None
    entry_date: Optional[date] = None
    gross_amount: Optional[Decimal] = None
    tds_amount: Optional[Decimal] = None
    notes: Optional[str] = None


class IncomeEntry(IncomeEntryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    net_amount: Decimal
    source_name: Optional[str] = None
    source_category: Optional[str] = None

    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class IncomeFYSummary(BaseModel):
    financial_year: str
    total_gross: Decimal
    total_tds: Decimal
    total_net: Decimal
    source_breakdown: List[Dict[str, Any]] = []

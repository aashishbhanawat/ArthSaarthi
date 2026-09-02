import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator
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
    tds_amount: Decimal = Field(
        default=Decimal("0.00"), ge=0, description="TDS deducted at source"
    )
    notes: Optional[str] = None

    # FR16.5: Optional Salary Breakdown fields
    basic_amount: Optional[Decimal] = Field(default=None, ge=0)
    hra_amount: Optional[Decimal] = Field(default=None, ge=0)
    da_amount: Optional[Decimal] = Field(default=None, ge=0)
    special_allowance_amount: Optional[Decimal] = Field(default=None, ge=0)
    other_allowances_amount: Optional[Decimal] = Field(default=None, ge=0)
    other_benefits_amount: Optional[Decimal] = Field(default=None, ge=0)
    rent_paid: Optional[Decimal] = Field(default=None, ge=0)
    is_metro: Optional[bool] = False

    @validator("tds_amount")
    def tds_must_not_exceed_gross(cls, v, values):
        if "gross_amount" in values and values["gross_amount"] is not None:
            if v > values["gross_amount"]:
                raise ValueError("TDS amount cannot exceed gross income amount")
        return v

    @validator("hra_amount")
    def hra_must_not_exceed_gross(cls, v, values):
        if (
            v is not None
            and "gross_amount" in values
            and values["gross_amount"] is not None
        ):
            if v > values["gross_amount"]:
                raise ValueError("HRA amount cannot exceed gross income amount")
        return v

    @validator("basic_amount")
    def basic_must_not_exceed_gross(cls, v, values):
        if (
            v is not None
            and "gross_amount" in values
            and values["gross_amount"] is not None
        ):
            if v > values["gross_amount"]:
                raise ValueError("Basic amount cannot exceed gross income amount")
        return v

    @root_validator(skip_on_failure=True)
    def salary_components_sum_must_not_exceed_gross(cls, values):
        gross = values.get("gross_amount")
        if gross is None:
            return values

        basic = values.get("basic_amount") or Decimal("0")
        hra = values.get("hra_amount") or Decimal("0")
        da = values.get("da_amount") or Decimal("0")
        spec = values.get("special_allowance_amount") or Decimal("0")
        other_allow = values.get("other_allowances_amount") or Decimal("0")
        other_ben = values.get("other_benefits_amount") or Decimal("0")

        total_components = basic + hra + da + spec + other_allow + other_ben
        if total_components > gross:
            raise ValueError(
                "Sum of salary components cannot exceed gross income amount"
            )
        return values


class IncomeEntryCreate(IncomeEntryBase):
    pass


class IncomeEntryUpdate(BaseModel):
    source_id: Optional[uuid.UUID] = None
    financial_year: Optional[str] = None
    entry_date: Optional[date] = None
    gross_amount: Optional[Decimal] = None
    tds_amount: Optional[Decimal] = None
    notes: Optional[str] = None

    basic_amount: Optional[Decimal] = Field(default=None, ge=0)
    hra_amount: Optional[Decimal] = Field(default=None, ge=0)
    da_amount: Optional[Decimal] = Field(default=None, ge=0)
    special_allowance_amount: Optional[Decimal] = Field(default=None, ge=0)
    other_allowances_amount: Optional[Decimal] = Field(default=None, ge=0)
    other_benefits_amount: Optional[Decimal] = Field(default=None, ge=0)
    rent_paid: Optional[Decimal] = Field(default=None, ge=0)
    is_metro: Optional[bool] = None


class IncomeEntry(IncomeEntryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    net_amount: Decimal
    hra_exemption: Optional[Decimal] = Decimal("0.00")
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
    total_hra_exemption: Optional[Decimal] = Decimal("0.00")
    source_breakdown: List[Dict[str, Any]] = []


import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.version import VERSION

try:
    if VERSION.startswith("2."):
        from pydantic import ConfigDict
    else:
        raise ImportError
except ImportError:
    ConfigDict = None


class TaxDeductionBase(BaseModel):
    financial_year: str = Field(..., description="e.g. 2025-2026")
    section: str = Field(..., description="Deduction section e.g. 80C, 80D")
    title: str = Field(..., min_length=1, description="Description e.g. LIC")
    amount: Decimal = Field(..., gt=0, description="Amount in INR")
    deduction_date: date = Field(..., description="Payment date")
    proof_notes: Optional[str] = Field(None, description="Proof note")


class TaxDeductionCreate(TaxDeductionBase):
    pass


class TaxDeductionUpdate(BaseModel):
    financial_year: Optional[str] = None
    section: Optional[str] = None
    title: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    deduction_date: Optional[date] = None
    proof_notes: Optional[str] = None


class TaxDeductionResponse(TaxDeductionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class SectionLimitSummary(BaseModel):
    section: str
    section_name: str
    total_invested: Decimal
    max_limit: Optional[Decimal] = None
    eligible_deduction: Decimal


class TaxDeductionFYSummary(BaseModel):
    financial_year: str
    total_invested: Decimal
    total_eligible_deduction: Decimal
    sections: List[SectionLimitSummary] = []

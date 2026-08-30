from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.core.tax_rules_registry import MANDATORY_TAX_DISCLAIMER


class IncomeSummary(BaseModel):
    gross_salary: Decimal = Field(default=Decimal("0.00"))
    business_income: Decimal = Field(default=Decimal("0.00"))
    dividend_income: Decimal = Field(default=Decimal("0.00"))
    other_income: Decimal = Field(default=Decimal("0.00"))
    total_gross_income: Decimal = Field(default=Decimal("0.00"))
    total_tds_credits: Decimal = Field(default=Decimal("0.00"))


class ExemptionsSummary(BaseModel):
    standard_deduction: Decimal = Field(default=Decimal("0.00"))
    hra_exemption: Decimal = Field(default=Decimal("0.00"))
    professional_tax: Decimal = Field(default=Decimal("0.00"))
    children_education_allowance: Decimal = Field(default=Decimal("0.00"))
    employer_nps: Decimal = Field(default=Decimal("0.00"))
    total_exemptions: Decimal = Field(default=Decimal("0.00"))


class DeductionSummary(BaseModel):
    section_80c: Decimal = Field(default=Decimal("0.00"))
    section_80d: Decimal = Field(default=Decimal("0.00"))
    section_80ccd_1b: Decimal = Field(default=Decimal("0.00"))
    section_80e: Decimal = Field(default=Decimal("0.00"))
    section_80g: Decimal = Field(default=Decimal("0.00"))
    section_80tta_80ttb: Decimal = Field(default=Decimal("0.00"))
    other_deductions: Decimal = Field(default=Decimal("0.00"))
    total_chapter_via_deductions: Decimal = Field(default=Decimal("0.00"))


class CapitalGainsSummary(BaseModel):
    stcg_taxable: Decimal = Field(default=Decimal("0.00"))
    ltcg_taxable: Decimal = Field(default=Decimal("0.00"))
    stcg_tax: Decimal = Field(default=Decimal("0.00"))
    ltcg_tax: Decimal = Field(default=Decimal("0.00"))
    total_capital_gains_tax: Decimal = Field(default=Decimal("0.00"))


class RegimeCalculation(BaseModel):
    regime_type: str  # "OLD" or "NEW"
    gross_income: Decimal = Field(default=Decimal("0.00"))
    exemptions: Decimal = Field(default=Decimal("0.00"))
    chapter_via_deductions: Decimal = Field(default=Decimal("0.00"))
    taxable_income: Decimal = Field(default=Decimal("0.00"))
    tax_on_slabs: Decimal = Field(default=Decimal("0.00"))
    capital_gains_tax: Decimal = Field(default=Decimal("0.00"))
    section_87a_rebate: Decimal = Field(default=Decimal("0.00"))
    tax_after_rebate: Decimal = Field(default=Decimal("0.00"))
    cess: Decimal = Field(default=Decimal("0.00"))
    total_tax_liability: Decimal = Field(default=Decimal("0.00"))
    tds_credits: Decimal = Field(default=Decimal("0.00"))
    net_tax_payable: Decimal = Field(default=Decimal("0.00"))


class TaxSummaryResponse(BaseModel):
    financial_year: str
    user_id: int
    income_summary: IncomeSummary
    exemptions_summary_old: ExemptionsSummary
    exemptions_summary_new: ExemptionsSummary
    deduction_summary: DeductionSummary
    capital_gains_summary: CapitalGainsSummary
    old_regime: RegimeCalculation
    new_regime: RegimeCalculation
    recommended_regime: str  # "OLD" or "NEW"
    tax_savings: Decimal = Field(default=Decimal("0.00"))
    disclaimer: str = Field(default=MANDATORY_TAX_DISCLAIMER)

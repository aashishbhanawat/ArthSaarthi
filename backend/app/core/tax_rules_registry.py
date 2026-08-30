from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

MANDATORY_TAX_DISCLAIMER: str = (
    "This Tax Readiness Summary and Tax Estimation tool is provided strictly for "
    "informational, educational, and tax/investment planning purposes only. The "
    "estimated tax calculations shown do NOT represent actual final tax liabilities "
    "payable to the Income Tax Department. For actual tax calculations and filing ITR, "
    "users must consult a qualified Chartered Accountant (CA) or tax consultant."
)


class FinancialYearTaxRules(BaseModel):
    financial_year: str
    old_regime_standard_deduction: Decimal
    new_regime_standard_deduction: Decimal
    section_87a_old_limit: Decimal
    section_87a_new_limit: Decimal
    section_87a_old_max_rebate: Decimal
    section_87a_new_max_rebate: Decimal
    # Each slab is (min_taxable_income, max_taxable_income_or_None, rate_decimal)
    old_regime_slabs: List[Tuple[Decimal, Optional[Decimal], Decimal]]
    new_regime_slabs: List[Tuple[Decimal, Optional[Decimal], Decimal]]
    health_and_education_cess_rate: Decimal = Field(default=Decimal("0.04"))
    disclaimer: str = Field(default=MANDATORY_TAX_DISCLAIMER)


OLD_REGIME_SLABS_DEFAULT: List[Tuple[Decimal, Optional[Decimal], Decimal]] = [
    (Decimal("0"), Decimal("250000"), Decimal("0.00")),
    (Decimal("250000"), Decimal("500000"), Decimal("0.05")),
    (Decimal("500000"), Decimal("1000000"), Decimal("0.20")),
    (Decimal("1000000"), None, Decimal("0.30")),
]

TAX_RULES_BY_FY: Dict[str, FinancialYearTaxRules] = {
    "2021-22": FinancialYearTaxRules(
        financial_year="2021-22",
        old_regime_standard_deduction=Decimal("50000"),
        new_regime_standard_deduction=Decimal("0"),
        section_87a_old_limit=Decimal("500000"),
        section_87a_new_limit=Decimal("500000"),
        section_87a_old_max_rebate=Decimal("12500"),
        section_87a_new_max_rebate=Decimal("12500"),
        old_regime_slabs=OLD_REGIME_SLABS_DEFAULT,
        new_regime_slabs=[
            (Decimal("0"), Decimal("250000"), Decimal("0.00")),
            (Decimal("250000"), Decimal("500000"), Decimal("0.05")),
            (Decimal("500000"), Decimal("750000"), Decimal("0.10")),
            (Decimal("750000"), Decimal("1000000"), Decimal("0.15")),
            (Decimal("1000000"), Decimal("1250000"), Decimal("0.20")),
            (Decimal("1250000"), Decimal("1500000"), Decimal("0.25")),
            (Decimal("1500000"), None, Decimal("0.30")),
        ],
    ),
    "2022-23": FinancialYearTaxRules(
        financial_year="2022-23",
        old_regime_standard_deduction=Decimal("50000"),
        new_regime_standard_deduction=Decimal("0"),
        section_87a_old_limit=Decimal("500000"),
        section_87a_new_limit=Decimal("500000"),
        section_87a_old_max_rebate=Decimal("12500"),
        section_87a_new_max_rebate=Decimal("12500"),
        old_regime_slabs=OLD_REGIME_SLABS_DEFAULT,
        new_regime_slabs=[
            (Decimal("0"), Decimal("250000"), Decimal("0.00")),
            (Decimal("250000"), Decimal("500000"), Decimal("0.05")),
            (Decimal("500000"), Decimal("750000"), Decimal("0.10")),
            (Decimal("750000"), Decimal("1000000"), Decimal("0.15")),
            (Decimal("1000000"), Decimal("1250000"), Decimal("0.20")),
            (Decimal("1250000"), Decimal("1500000"), Decimal("0.25")),
            (Decimal("1500000"), None, Decimal("0.30")),
        ],
    ),
    "2023-24": FinancialYearTaxRules(
        financial_year="2023-24",
        old_regime_standard_deduction=Decimal("50000"),
        new_regime_standard_deduction=Decimal("50000"),
        section_87a_old_limit=Decimal("500000"),
        section_87a_new_limit=Decimal("700000"),
        section_87a_old_max_rebate=Decimal("12500"),
        section_87a_new_max_rebate=Decimal("25000"),
        old_regime_slabs=OLD_REGIME_SLABS_DEFAULT,
        new_regime_slabs=[
            (Decimal("0"), Decimal("300000"), Decimal("0.00")),
            (Decimal("300000"), Decimal("600000"), Decimal("0.05")),
            (Decimal("600000"), Decimal("900000"), Decimal("0.10")),
            (Decimal("900000"), Decimal("1200000"), Decimal("0.15")),
            (Decimal("1200000"), Decimal("1500000"), Decimal("0.20")),
            (Decimal("1500000"), None, Decimal("0.30")),
        ],
    ),
    "2024-25": FinancialYearTaxRules(
        financial_year="2024-25",
        old_regime_standard_deduction=Decimal("50000"),
        new_regime_standard_deduction=Decimal("75000"),
        section_87a_old_limit=Decimal("500000"),
        section_87a_new_limit=Decimal("700000"),
        section_87a_old_max_rebate=Decimal("12500"),
        section_87a_new_max_rebate=Decimal("25000"),
        old_regime_slabs=OLD_REGIME_SLABS_DEFAULT,
        new_regime_slabs=[
            (Decimal("0"), Decimal("300000"), Decimal("0.00")),
            (Decimal("300000"), Decimal("700000"), Decimal("0.05")),
            (Decimal("700000"), Decimal("1000000"), Decimal("0.10")),
            (Decimal("1000000"), Decimal("1200000"), Decimal("0.15")),
            (Decimal("1200000"), Decimal("1500000"), Decimal("0.20")),
            (Decimal("1500000"), None, Decimal("0.30")),
        ],
    ),
    "2025-26": FinancialYearTaxRules(
        financial_year="2025-26",
        old_regime_standard_deduction=Decimal("50000"),
        new_regime_standard_deduction=Decimal("75000"),
        section_87a_old_limit=Decimal("500000"),
        section_87a_new_limit=Decimal("750000"),
        section_87a_old_max_rebate=Decimal("12500"),
        section_87a_new_max_rebate=Decimal("25000"),
        old_regime_slabs=OLD_REGIME_SLABS_DEFAULT,
        new_regime_slabs=[
            (Decimal("0"), Decimal("300000"), Decimal("0.00")),
            (Decimal("300000"), Decimal("700000"), Decimal("0.05")),
            (Decimal("700000"), Decimal("1000000"), Decimal("0.10")),
            (Decimal("1000000"), Decimal("1200000"), Decimal("0.15")),
            (Decimal("1200000"), Decimal("1500000"), Decimal("0.20")),
            (Decimal("1500000"), None, Decimal("0.30")),
        ],
    ),
    "2026-27": FinancialYearTaxRules(
        financial_year="2026-27",
        old_regime_standard_deduction=Decimal("50000"),
        new_regime_standard_deduction=Decimal("75000"),
        section_87a_old_limit=Decimal("500000"),
        section_87a_new_limit=Decimal("750000"),
        section_87a_old_max_rebate=Decimal("12500"),
        section_87a_new_max_rebate=Decimal("25000"),
        old_regime_slabs=OLD_REGIME_SLABS_DEFAULT,
        new_regime_slabs=[
            (Decimal("0"), Decimal("300000"), Decimal("0.00")),
            (Decimal("300000"), Decimal("700000"), Decimal("0.05")),
            (Decimal("700000"), Decimal("1000000"), Decimal("0.10")),
            (Decimal("1000000"), Decimal("1200000"), Decimal("0.15")),
            (Decimal("1200000"), Decimal("1500000"), Decimal("0.20")),
            (Decimal("1500000"), None, Decimal("0.30")),
        ],
    ),
}


def get_fy_variations(financial_year: str) -> List[str]:
    """Return both short ('2026-27') and long ('2026-2027') variations for FY matching."""
    parts = financial_year.strip().split("-")
    if len(parts) == 2:
        start, end = parts[0], parts[1]
        if len(start) == 4:
            if len(end) == 2:
                return [financial_year, f"{start}-{start[:2]}{end}"]
            elif len(end) == 4:
                return [f"{start}-{end[-2:]}", financial_year]
    return [financial_year]


def get_tax_rules(financial_year: str) -> FinancialYearTaxRules:
    """Retrieve statutory tax rules for a specified financial year."""
    for fy in get_fy_variations(financial_year):
        if fy in TAX_RULES_BY_FY:
            return TAX_RULES_BY_FY[fy]
    return TAX_RULES_BY_FY["2024-25"]


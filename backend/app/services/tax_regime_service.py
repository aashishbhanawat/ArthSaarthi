import uuid
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.tax_rules_registry import (
    MANDATORY_TAX_DISCLAIMER,
    FinancialYearTaxRules,
    get_tax_rules,
)
from app.crud.crud_income import crud_income_entry
from app.crud.crud_tax_deduction import crud_tax_deduction
from app.schemas.tax_summary import (
    CapitalGainsSummary,
    DeductionSummary,
    ExemptionsSummary,
    IncomeSummary,
    RegimeCalculation,
    TaxSummaryResponse,
)


class TaxRegimeService:
    @staticmethod
    def _calculate_slab_tax(
        taxable_income: Decimal,
        slabs: list[Tuple[Decimal, Optional[Decimal], Decimal]],
    ) -> Decimal:
        """Calculate tax on taxable income based on tax slabs."""
        if taxable_income <= Decimal("0.00"):
            return Decimal("0.00")

        tax = Decimal("0.00")
        for min_inc, max_inc, rate in slabs:
            if taxable_income > min_inc:
                if max_inc is not None:
                    bracket_income = min(taxable_income, max_inc) - min_inc
                else:
                    bracket_income = taxable_income - min_inc
                tax += bracket_income * rate

        return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def compute_tax_summary(
        cls,
        db: Session,
        *,
        user_id: uuid.UUID,
        financial_year: str = "2024-25",
    ) -> TaxSummaryResponse:
        rules: FinancialYearTaxRules = get_tax_rules(financial_year)

        # 1. Fetch Income Summary
        income_data = crud_income_entry.get_summary_by_fy(
            db, user_id=user_id, financial_year=financial_year
        )
        gross_salary = Decimal("0.00")
        business_income = Decimal("0.00")
        dividend_income = Decimal("0.00")
        other_income = Decimal("0.00")
        total_tds = Decimal(str(income_data.get("total_tds", "0.00")))

        for sb in income_data.get("source_breakdown", []):
            cat = (sb.get("category") or "").upper()
            gross = Decimal(str(sb.get("gross_amount", "0.00")))
            if cat == "SALARY":
                gross_salary += gross
            elif cat == "BUSINESS":
                business_income += gross
            elif cat == "DIVIDEND":
                dividend_income += gross
            else:
                other_income += gross

        total_gross_income = (
            gross_salary + business_income + dividend_income + other_income
        )

        income_summary = IncomeSummary(
            gross_salary=gross_salary,
            business_income=business_income,
            dividend_income=dividend_income,
            other_income=other_income,
            total_gross_income=total_gross_income,
            total_tds_credits=total_tds,
        )

        # 2. Fetch Chapter VI-A Deductions Summary
        deduction_data = crud_tax_deduction.get_summary_by_fy(
            db, user_id=user_id, financial_year=financial_year
        )

        sec_80c = Decimal("0.00")
        sec_80d = Decimal("0.00")
        sec_80ccd_1b = Decimal("0.00")
        sec_80e = Decimal("0.00")
        sec_80g = Decimal("0.00")
        sec_80tta_ttb = Decimal("0.00")
        other_ded = Decimal("0.00")

        for sec in deduction_data.get("sections", []):
            s_code = (sec.get("section") or "").upper()
            elig = Decimal(str(sec.get("eligible_deduction", "0.00")))
            if s_code == "80C":
                sec_80c += elig
            elif s_code == "80D":
                sec_80d += elig
            elif s_code == "80CCD_1B":
                sec_80ccd_1b += elig
            elif s_code == "80E":
                sec_80e += elig
            elif s_code == "80G":
                sec_80g += elig
            elif s_code in ["80TTA", "80TTB"]:
                sec_80tta_ttb += elig
            else:
                other_ded += elig

        total_chapter_via = Decimal(
            str(deduction_data.get("total_eligible_deduction", "0.00"))
        )

        deduction_summary = DeductionSummary(
            section_80c=sec_80c,
            section_80d=sec_80d,
            section_80ccd_1b=sec_80ccd_1b,
            section_80e=sec_80e,
            section_80g=sec_80g,
            section_80tta_80ttb=sec_80tta_ttb,
            other_deductions=other_ded,
            total_chapter_via_deductions=total_chapter_via,
        )

        # 3. Capital Gains Summary (placeholder / baseline 0.00 until integrated)
        capital_gains_summary = CapitalGainsSummary(
            stcg_taxable=Decimal("0.00"),
            ltcg_taxable=Decimal("0.00"),
            stcg_tax=Decimal("0.00"),
            ltcg_tax=Decimal("0.00"),
            total_capital_gains_tax=Decimal("0.00"),
        )

        # 4. Compute Old Regime
        # Standard deduction applies to salary income (or gross if salary isn't split)
        old_std_ded = min(
            gross_salary if gross_salary > 0 else total_gross_income,
            rules.old_regime_standard_deduction,
        )
        total_hra_exemption = Decimal(
            str(income_data.get("total_hra_exemption", "0.00"))
        )
        old_exemptions_summary = ExemptionsSummary(
            standard_deduction=old_std_ded,
            hra_exemption=total_hra_exemption,
            professional_tax=Decimal("0.00"),
            children_education_allowance=Decimal("0.00"),
            employer_nps=Decimal("0.00"),
            total_exemptions=old_std_ded + total_hra_exemption,
        )

        old_taxable_income = max(
            Decimal("0.00"),
            total_gross_income
            - old_exemptions_summary.total_exemptions
            - total_chapter_via,
        )

        old_slab_tax = cls._calculate_slab_tax(
            old_taxable_income, rules.old_regime_slabs
        )

        # Section 87A rebate for Old Regime
        if old_taxable_income <= rules.section_87a_old_limit:
            old_rebate = min(old_slab_tax, rules.section_87a_old_max_rebate)
        else:
            old_rebate = Decimal("0.00")

        old_tax_after_rebate = max(Decimal("0.00"), old_slab_tax - old_rebate)
        cess_rate = rules.health_and_education_cess_rate
        old_cess = (old_tax_after_rebate * cess_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        old_total_tax = old_tax_after_rebate + old_cess
        old_net_payable = old_total_tax - total_tds

        old_regime = RegimeCalculation(
            regime_type="OLD",
            gross_income=total_gross_income,
            exemptions=old_std_ded,
            chapter_via_deductions=total_chapter_via,
            taxable_income=old_taxable_income,
            tax_on_slabs=old_slab_tax,
            capital_gains_tax=Decimal("0.00"),
            section_87a_rebate=old_rebate,
            tax_after_rebate=old_tax_after_rebate,
            cess=old_cess,
            total_tax_liability=old_total_tax,
            tds_credits=total_tds,
            net_tax_payable=old_net_payable,
        )

        # 5. Compute New Regime
        new_std_ded = min(
            gross_salary if gross_salary > 0 else total_gross_income,
            rules.new_regime_standard_deduction,
        )
        new_exemptions_summary = ExemptionsSummary(
            standard_deduction=new_std_ded,
            hra_exemption=Decimal("0.00"),
            professional_tax=Decimal("0.00"),
            children_education_allowance=Decimal("0.00"),
            employer_nps=Decimal("0.00"),
            total_exemptions=new_std_ded,
        )

        new_taxable_income = max(
            Decimal("0.00"),
            total_gross_income - new_std_ded,
        )

        new_slab_tax = cls._calculate_slab_tax(
            new_taxable_income, rules.new_regime_slabs
        )

        # Section 87A rebate for New Regime
        if new_taxable_income <= rules.section_87a_new_limit:
            new_rebate = min(new_slab_tax, rules.section_87a_new_max_rebate)
        else:
            new_rebate = Decimal("0.00")

        new_tax_after_rebate = max(Decimal("0.00"), new_slab_tax - new_rebate)
        new_cess = (new_tax_after_rebate * cess_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        new_total_tax = new_tax_after_rebate + new_cess
        new_net_payable = new_total_tax - total_tds

        new_regime = RegimeCalculation(
            regime_type="NEW",
            gross_income=total_gross_income,
            exemptions=new_std_ded,
            chapter_via_deductions=Decimal("0.00"),
            taxable_income=new_taxable_income,
            tax_on_slabs=new_slab_tax,
            capital_gains_tax=Decimal("0.00"),
            section_87a_rebate=new_rebate,
            tax_after_rebate=new_tax_after_rebate,
            cess=new_cess,
            total_tax_liability=new_total_tax,
            tds_credits=total_tds,
            net_tax_payable=new_net_payable,
        )

        # 6. Recommendation & Savings Calculation
        if new_total_tax <= old_total_tax:
            recommended_regime = "NEW"
            tax_savings = old_total_tax - new_total_tax
        else:
            recommended_regime = "OLD"
            tax_savings = new_total_tax - old_total_tax

        return TaxSummaryResponse(
            financial_year=financial_year,
            user_id=1,  # int format for API response schema
            income_summary=income_summary,
            exemptions_summary_old=old_exemptions_summary,
            exemptions_summary_new=new_exemptions_summary,
            deduction_summary=deduction_summary,
            capital_gains_summary=capital_gains_summary,
            old_regime=old_regime,
            new_regime=new_regime,
            recommended_regime=recommended_regime,
            tax_savings=tax_savings,
            disclaimer=MANDATORY_TAX_DISCLAIMER,
        )

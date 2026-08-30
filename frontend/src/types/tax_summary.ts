export interface IncomeSummary {
  gross_salary: number;
  business_income: number;
  dividend_income: number;
  other_income: number;
  total_gross_income: number;
  total_tds_credits: number;
}

export interface ExemptionsSummary {
  standard_deduction: number;
  hra_exemption: number;
  professional_tax: number;
  children_education_allowance: number;
  employer_nps: number;
  total_exemptions: number;
}

export interface DeductionSummary {
  section_80c: number;
  section_80d: number;
  section_80ccd_1b: number;
  section_80e: number;
  section_80g: number;
  section_80tta_80ttb: number;
  other_deductions: number;
  total_chapter_via_deductions: number;
}

export interface CapitalGainsSummary {
  stcg_taxable: number;
  ltcg_taxable: number;
  stcg_tax: number;
  ltcg_tax: number;
  total_capital_gains_tax: number;
}

export interface RegimeCalculation {
  regime_type: 'OLD' | 'NEW';
  gross_income: number;
  exemptions: number;
  chapter_via_deductions: number;
  taxable_income: number;
  tax_on_slabs: number;
  capital_gains_tax: number;
  section_87a_rebate: number;
  tax_after_rebate: number;
  cess: number;
  total_tax_liability: number;
  tds_credits: number;
  net_tax_payable: number;
}

export interface TaxSummaryResponse {
  financial_year: string;
  user_id: number;
  income_summary: IncomeSummary;
  exemptions_summary_old: ExemptionsSummary;
  exemptions_summary_new: ExemptionsSummary;
  deduction_summary: DeductionSummary;
  capital_gains_summary: CapitalGainsSummary;
  old_regime: RegimeCalculation;
  new_regime: RegimeCalculation;
  recommended_regime: 'OLD' | 'NEW';
  tax_savings: number;
  disclaimer: string;
}

export interface TaxDeduction {
  id: string;
  user_id: string;
  financial_year: string;
  section: string;
  title: string;
  amount: number | string;
  deduction_date: string;
  proof_notes?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface TaxDeductionCreate {
  financial_year: string;
  section: string;
  title: string;
  amount: number;
  deduction_date: string;
  proof_notes?: string;
}

export interface TaxDeductionUpdate {
  financial_year?: string;
  section?: string;
  title?: string;
  amount?: number;
  deduction_date?: string;
  proof_notes?: string;
}

export interface SectionLimitSummary {
  section: string;
  section_name: string;
  total_invested: number;
  max_limit: number | null;
  eligible_deduction: number;
}

export interface TaxDeductionFYSummary {
  financial_year: string;
  total_invested: number;
  total_eligible_deduction: number;
  sections: SectionLimitSummary[];
}

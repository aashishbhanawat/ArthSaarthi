export type IncomeCategory =
  | 'SALARY'
  | 'FREELANCE'
  | 'RENTAL'
  | 'DIVIDEND'
  | 'INTEREST'
  | 'BUSINESS'
  | 'OTHER';

export interface IncomeSource {
  id: string;
  user_id: string;
  name: string;
  category: IncomeCategory;
  payer_name?: string | null;
}

export interface IncomeSourcePayload {
  name: string;
  category: IncomeCategory;
  payer_name?: string | null;
}

export interface IncomeEntry {
  id: string;
  user_id: string;
  source_id: string;
  financial_year: string;
  entry_date: string;
  gross_amount: number;
  tds_amount: number;
  net_amount: number;
  notes?: string | null;
  source_name?: string | null;
  source_category?: IncomeCategory | null;
}

export interface IncomeEntryPayload {
  source_id: string;
  financial_year: string;
  entry_date: string;
  gross_amount: number;
  tds_amount: number;
  notes?: string | null;
}

export interface IncomeSourceBreakdown {
  source_id: string;
  source_name: string;
  category: IncomeCategory;
  gross_amount: number;
  tds_amount: number;
  net_amount: number;
  count: number;
}

export interface IncomeFYSummary {
  financial_year: string;
  total_gross: number;
  total_tds: number;
  total_net: number;
  source_breakdown: IncomeSourceBreakdown[];
}

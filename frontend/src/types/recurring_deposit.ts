export interface RecurringDepositBase {
  name: string;
  account_number: string;
  monthly_installment: number;
  interest_rate: number;
  start_date: string; // Dates are typically strings in ISO format
  tenure_months: number;
}

export interface RecurringDeposit extends RecurringDepositBase {
  id: string;
  portfolio_id: string;
  user_id: string;
}

export interface RecurringDepositDetails extends RecurringDeposit {
  maturity_value: number;
}

export interface RecurringDepositAnalytics {
  unrealized_xirr: number;
}

export interface RecurringDepositCreate extends RecurringDepositBase {}

export interface RecurringDepositUpdate extends Partial<RecurringDepositBase> {}

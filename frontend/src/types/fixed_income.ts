export interface FixedDepositCreate {
  institution_name: string;
  account_number?: string;
  principal_amount: number;
  interest_rate: number;
  start_date: string; // YYYY-MM-DD
  maturity_date: string; // YYYY-MM-DD
  payout_type: 'REINVESTMENT' | 'PAYOUT';
  compounding_frequency: 'MONTHLY' | 'QUARTERLY' | 'HALF_YEARLY' | 'ANNUALLY' | 'AT_MATURITY';
}

export interface BondCreate {
    bond_name: string;
    isin?: string;
    face_value: number;
    coupon_rate: number;
    purchase_price: number;
    purchase_date: string; // YYYY-MM-DD
    maturity_date: string; // YYYY-MM-DD
    interest_payout_frequency: 'ANNUALLY' | 'SEMI_ANNUALLY';
    quantity: number;
}

export interface PublicProvidentFundCreate {
    institution_name: string;
    account_number?: string;
    opening_date: string; // YYYY-MM-DD
    current_balance: number;
}

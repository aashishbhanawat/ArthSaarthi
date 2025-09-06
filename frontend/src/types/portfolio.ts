import { Asset } from './asset';

export interface Transaction {
  id: string;
  asset_id: string;
  portfolio_id: string;
  transaction_type: 'BUY' | 'SELL';
  quantity: string;
  price_per_unit: string;
  fees: string;
  transaction_date: string; // ISO 8601 date string
  asset: Asset;
}

export interface Portfolio {
  id: string;
  name: string;
  description: string | null;
  transactions: Transaction[];
}

export interface PortfolioCreate {
  name: string;
  description?: string | null;
}

export type TransactionCreate = {
  transaction_type: 'BUY' | 'SELL';
  quantity: number;
  price_per_unit: number;
  transaction_date: string;
  fees?: number;
} & ({ asset_id: string } | { ticker_symbol: string; asset_type: string });

export interface TransactionUpdate {
  transaction_type?: 'BUY' | 'SELL';
  quantity?: number;
  price_per_unit?: number;
  transaction_date?: string;
  fees?: number;
  asset_id?: string;
}

export interface TransactionsResponse {
  transactions: Transaction[];
  total: number;
}

export interface FixedDepositCreate {
    name: string;
    principal_amount: number;
    interest_rate: number;
    start_date: string;
    maturity_date: string;
    compounding_frequency: 'Annually' | 'Half-Yearly' | 'Quarterly';
    interest_payout: 'Cumulative' | 'Payout';
}

export interface FixedDeposit extends FixedDepositCreate {
    id: string;
    portfolio_id: string;
    user_id: string;
}

export interface FixedDepositDetails extends FixedDeposit {
    maturity_value: number;
}

export interface FixedDepositAnalytics {
    unrealized_xirr: number;
    realized_xirr: number;
}
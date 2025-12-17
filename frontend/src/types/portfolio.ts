import { Asset } from './asset';
import { TransactionType } from './enums';

export interface Transaction {
  id: string;
  asset_id: string;
  portfolio_id: string;
  transaction_type: TransactionType;
  quantity: string;
  price_per_unit: string;
  fees: string;
  transaction_date: string; // ISO 8601 date string
  asset: Asset;
  is_reinvested: boolean;
  details?: Record<string, unknown> | null;
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

export interface TransactionLinkCreate {
  buy_transaction_id: string;
  quantity: number;
}

export type TransactionCreate = {
  transaction_type: TransactionType;
  quantity: number;
  price_per_unit: number;
  transaction_date: string;
  fees?: number;
  is_reinvested?: boolean;
  details?: Record<string, unknown>;
  links?: TransactionLinkCreate[];
} & ({ asset_id: string; ticker_symbol?: never; asset_type?: never; } | { asset_id?: never; ticker_symbol: string; asset_type: string });


export interface TransactionUpdate {
  transaction_type?: TransactionType;
  quantity?: number;
  price_per_unit?: number;
  transaction_date?: string;
  fees?: number;
  asset_id?: string;
  details?: Record<string, unknown>;
  links?: TransactionLinkCreate[];
}

export interface TransactionsResponse {
  transactions: Transaction[];
  total: number;
}

export interface TransactionCreatedResponse {
  created_transactions: Transaction[];
}

export interface FixedDepositCreate {
  name: string;
  principal_amount: number;
  interest_rate: number;
  start_date: string;
  maturity_date: string;
  compounding_frequency: 'Annually' | 'Half-Yearly' | 'Quarterly';
  interest_payout: 'Cumulative' | 'Payout';
  account_number?: string;
}

export interface FixedDepositUpdate {
  name?: string;
  principal_amount?: number;
  interest_rate?: number;
  start_date?: string;
  maturity_date?: string;
  compounding_frequency?: 'Annually' | 'Half-Yearly' | 'Quarterly';
  interest_payout?: 'Cumulative' | 'Payout';
  account_number?: string;
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

export interface PpfCreate {
  institution_name: string;
  account_number?: string;
  opening_date: string;
  amount: number;
  contribution_date: string;
}

import { Asset } from './asset';

export interface Transaction {
  id: string;
  asset_id: string;
  portfolio_id: string;
  transaction_type: 'BUY' | 'SELL';
  quantity: number;
  price_per_unit: number;
  fees: number;
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

export interface TransactionCreate {
  asset_id: string;
  transaction_type: 'BUY' | 'SELL';
  quantity: number;
  price_per_unit: number;
  transaction_date: string;
  fees?: number;
}

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
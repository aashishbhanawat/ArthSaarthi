import { Asset } from './asset';

export interface Transaction {
  id: string;
  asset_id: string;
  portfolio_id: string;
  transaction_type: 'BUY' | 'SELL';
  quantity: string; // Backend Decimal serializes to string
  price_per_unit: string; // Backend Decimal serializes to string
  fees: string; // Backend Decimal serializes to string
  transaction_date: string; // ISO date string
  asset: Asset;
}

export interface TransactionsResponse {
  transactions: Transaction[];
  total: number;
}
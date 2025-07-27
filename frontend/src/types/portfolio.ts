export interface Asset {
  id: number;
  ticker_symbol: string;
  name: string;
  asset_type: string;
  currency: string;
}

export interface Transaction {
  id: number;
  asset_id: number;
  portfolio_id: number;
  transaction_type: 'BUY' | 'SELL';
  quantity: number;
  price_per_unit: number;
  fees: number;
  transaction_date: string; // ISO 8601 date string
  asset: Asset;
}

export interface Portfolio {
  id: number;
  name: string;
  description: string | null;
  transactions: Transaction[];
}

export interface PortfolioCreate {
  name: string;
  description?: string | null;
}

export interface NewAsset {
    ticker_symbol: string;
    name: string;
    asset_type: string;
    currency: string;
}

export interface TransactionCreate {
    asset_id: number;
    transaction_type: 'BUY' | 'SELL';
    quantity: number;
    price_per_unit: number;
    transaction_date: string;
    fees?: number;
}
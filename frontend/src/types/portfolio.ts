export interface Asset {
  id: number;
  ticker_symbol: string;
  name: string;
  asset_type: string;
  currency: string;
}

export interface Transaction {
  id: number;
  transaction_type: 'BUY' | 'SELL';
  quantity: string; // Comes as a string from backend (Numeric)
  price_per_unit: string; // Comes as a string from backend (Numeric)
  fees: string; // Comes as a string from backend (Numeric)
  transaction_date: string; // ISO 8601 date string
  asset: Asset;
}

export interface Portfolio {
  id: number;
  name: string;
  user_id: number;
  transactions: Transaction[];
}

export interface PortfolioCreate {
  name: string;
}

export interface NewAsset {
    ticker_symbol: string;
    name: string;
    asset_type: string;
    currency: string;
}

export interface TransactionCreate {
    portfolio_id: number;
    asset_id?: number;
    new_asset?: NewAsset;
    transaction_type: 'BUY' | 'SELL';
    quantity: number;
    price_per_unit: number;
    transaction_date: string;
    fees?: number;
}
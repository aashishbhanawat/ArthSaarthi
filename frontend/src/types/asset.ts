export interface Asset {
    id: string;
    name: string;
    ticker_symbol: string;
    asset_type: string;
    isin: string | null;
    currency: string | null;
    exchange: string | null;
    current_price?: number;
    day_change?: number;
}

export interface MutualFundSearchResult {
    ticker_symbol: string;
    name: string;
    asset_type: 'Mutual Fund';
}

export interface PpfAccountCreate {
    name: string;
    asset_type: 'PPF';
    ticker_symbol: string;
    currency: string;
    account_number?: string;
    opening_date: string;
}
import { Bond } from './bond';

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
    account_number?: string | null;
    investment_style?: string | null; // Value, Growth, Blend
    bond?: Bond | null;
}

export interface MutualFundSearchResult {
    ticker_symbol: string;
    name: string;
    asset_type: 'Mutual Fund';
}
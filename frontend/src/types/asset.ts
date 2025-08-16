export interface Asset {
    id: string;
    name: string;
    ticker_symbol: string;
    asset_type: string;
    currency: string;
    exchange: string | null;
    isin: string | null;
}
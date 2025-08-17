export interface Asset {
    id: string;
    name: string;
    ticker_symbol: string;
    asset_type: string;
    isin: string | null;
    currency: string | null;
    exchange: string | null;
}
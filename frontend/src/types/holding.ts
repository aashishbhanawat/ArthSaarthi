export interface Holding {
    asset_id: string;
    ticker_symbol: string;
    asset_name: string;
    asset_type: string;
    group: string;
    quantity: number;
    average_buy_price: number;
    total_invested_amount: number;
    current_price: number;
    current_value: number;
    days_pnl: number;
    days_pnl_percentage: number;
    unrealized_pnl: number;
    unrealized_pnl_percentage: number;
    realized_pnl?: number;
    interest_rate: number | null;
    maturity_date: string | null;
    account_number: string | null;
    opening_date: string | null;
    isin: string;
}

export interface HoldingsResponse {
    holdings: Holding[];
}

export interface PortfolioSummary {
    total_value: number;
    total_invested_amount: number;
    days_pnl: number;
    total_unrealized_pnl: number;
    total_realized_pnl: number;
}
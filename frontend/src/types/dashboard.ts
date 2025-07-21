export interface DashboardAsset {
    ticker_symbol: string;
    current_price: string;
    price_change_24h: string;
    price_change_percentage_24h: string;
}

export interface DashboardSummary {
    total_value: string;
    total_unrealized_pnl: string;
    total_realized_pnl: string;
    top_movers: DashboardAsset[];
}
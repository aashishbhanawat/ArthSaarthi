export interface DashboardAsset {
    ticker_symbol: string;
    current_price: number;
    price_change_24h: number;
    price_change_percentage_24h: number;
}

export interface TopMover {
  ticker_symbol: string;
  name: string;
  current_price: number;
  daily_change: number;
  daily_change_percentage: number;
}

export interface DashboardSummary {
    total_value: number;
    total_unrealized_pnl: number;
    total_realized_pnl: number;
    top_movers: TopMover[];
    asset_allocation: AssetAllocation[];
}

export interface PortfolioHistoryPoint {
    date: string;
    value: number;
}

export interface PortfolioHistoryResponse {
    history: PortfolioHistoryPoint[];
}

export interface AssetAllocation {
    ticker: string;
    value: number;
}

export interface AssetAllocationResponse {
    allocation: AssetAllocation[];
}
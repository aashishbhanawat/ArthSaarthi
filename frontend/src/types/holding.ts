export interface Holding {
  asset_id: string;
  ticker_symbol: string;
  asset_name: string;
  quantity: number;
  average_buy_price: number;
  total_invested_amount: number;
  current_price: number;
  current_value: number;
  days_pnl: number;
  days_pnl_percentage: number;
  unrealized_pnl: number;
  unrealized_pnl_percentage: number;
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
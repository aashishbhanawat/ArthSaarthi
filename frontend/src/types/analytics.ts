export interface PortfolioAnalytics {
  total_value: number;
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  xirr: number | null;
  sharpe_ratio: number | null;
  realized_xirr?: number | null;
  unrealized_xirr?: number | null;
}

export interface PortfolioAnalytics {
  xirr: number;
  sharpe_ratio: number;
}

export interface AssetAnalytics {
  xirr_current: number;
  xirr_historical: number;
  realized_pnl: number;
  dividend_income: number;
}

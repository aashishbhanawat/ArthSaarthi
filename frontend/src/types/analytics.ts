export interface PortfolioAnalytics {
  xirr: number;
  sharpe_ratio: number;
}

export interface AssetAnalytics {
  realized_xirr: number;
  unrealized_xirr: number;
}

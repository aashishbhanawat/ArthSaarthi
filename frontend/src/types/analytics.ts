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

export interface DiversificationSegment {
  name: string;
  value: number;
  percentage: number;
  count: number;
}

export interface DiversificationResponse {
  by_asset_class: DiversificationSegment[];
  by_sector: DiversificationSegment[];
  by_industry: DiversificationSegment[];
  by_market_cap: DiversificationSegment[];
  by_country: DiversificationSegment[];
  by_investment_style: DiversificationSegment[];
  total_value: number;
}

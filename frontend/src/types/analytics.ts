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
  total_value: number;
}

// Capital Gains types (FR6.5)
export interface GainsBreakdown {
  gains: number;
  losses: number;
  net: number;
}

export interface TermBreakdown {
  short_term: GainsBreakdown;
  long_term: GainsBreakdown;
  total: GainsBreakdown;
}

export interface CapitalGainsHolding {
  asset_id: string;
  asset_name: string;
  ticker: string;
  first_buy_date: string | null;
  holding_period_days: number;
  term: 'short_term' | 'long_term';
  quantity: number;
  cost_basis: number;
  current_value: number;
  unrealized_gain: number;
}

export interface CapitalGainsResponse {
  unrealized: TermBreakdown;
  realized: TermBreakdown;
  holdings_breakdown: CapitalGainsHolding[];
}

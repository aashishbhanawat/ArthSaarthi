export interface MarketNewsMetadata {
  recommendation?: string;
  target_price?: number;
  broker?: string;
  quarter?: string;
  audio_url?: string;
  [key: string]: unknown;
}

export interface MarketNewsArticle {
  id: string;
  title: string;
  summary?: string | null;
  url: string;
  source: string;
  category: 'NEWS' | 'BROKER_REPORT' | 'CONCALL' | 'RESULT' | string;
  published_at: string;
  symbols: string[];
  sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL' | string;
  metadata_json?: MarketNewsMetadata | null;
  created_at: string;
}

export interface ResearchFeedResponse {
  items: MarketNewsArticle[];
  total: number;
  symbols: string[];
}

export interface ResearchFeedSummary {
  news_count: number;
  broker_reports_count: number;
  concalls_count: number;
  results_count: number;
  latest_items: MarketNewsArticle[];
}

export interface NewsRefreshResponse {
  message: string;
  articles_fetched: number;
  articles_inserted: number;
  status: string;
}

export interface ToneBreakdown {
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  overall: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | 'BALANCED' | string;
  average_tone_score?: number;
  sample_size: number;
}

export interface GuidanceMetric {
  category: string;
  text: string;
}

export interface RedFlagItem {
  text: string;
  score: number;
}

export interface ConcallAnalysis {
  article_id: string;
  title: string;
  quarter?: string | null;
  management_tone: ToneBreakdown;
  qa_tone: ToneBreakdown;
  tone_gap_alert?: number | null;
  tone_divergence_summary?: string | null;
  hedge_rate_per_100w?: number | null;
  topic_sentiment?: Record<string, number> | null;
  red_flags?: RedFlagItem[];
  guidance_metrics: GuidanceMetric[];
  top_takeaways: string[];
  key_themes: string[];
  transcription_source: 'TRANSCRIPT' | 'WHISPER_AUDIO' | 'USER_INPUT' | string;
}

export interface MarketNewsMetadata {
  recommendation?: string;
  target_price?: number;
  broker?: string;
  quarter?: string;
  audio_url?: string;
  transcript_url?: string;
  transcript_text?: string;
  action_type?: string;
  dividend_amount?: number;
  ex_date?: string;
  concall_analysis?: ConcallAnalysis;
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

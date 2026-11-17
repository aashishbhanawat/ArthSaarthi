export interface CorporateActionEventItem {
  id: string;
  user_id: string;
  portfolio_id: string;
  asset_id: string;
  transaction_id: string | null;
  event_type: 'BOND_COUPON' | 'BOND_MATURITY' | 'DIVIDEND' | 'SPLIT' | 'BONUS' | string;
  event_date: string;
  units: number;
  amount: number;
  status: 'NEW' | 'READ' | 'DISMISSED' | string;
  details: Record<string, unknown> | null;
  created_at: string;
  bond_name?: string | null;
  stock_name?: string | null;
  symbol?: string | null;
  isin?: string | null;
}

export interface CorporateActionEventListResponse {
  items: CorporateActionEventItem[];
  total: number;
  unread_count: number;
}

export interface CorporateActionTriggerResponse {
  message: string;
  events_created: number;
  status: string;
}

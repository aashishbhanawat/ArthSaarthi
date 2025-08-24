export interface WatchlistItem {
  id: string;
  asset_id: string;
}

export interface Watchlist {
  id: string;
  name: string;
  user_id: string;
  created_at: string;
  items: WatchlistItem[];
}

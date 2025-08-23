export interface WatchlistItem {
  id: string;
  watchlist_id: string;
  asset_id: string;
}

export interface Watchlist {
  id: string;
  name: string;
  user_id: string;
  items: WatchlistItem[];
}

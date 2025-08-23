import { Asset } from "./asset";

export interface WatchlistItem {
  id: string;
  watchlist_id: string;
  asset_id: string;
  asset: Asset;
}

export interface Watchlist {
  id: string;
  name: string;
  user_id: string;
  items: WatchlistItem[];
}

export interface WatchlistCreate {
  name: string;
}

export interface WatchlistUpdate {
  name: string;
}

export interface WatchlistItemCreate {
  asset_id: string;
}

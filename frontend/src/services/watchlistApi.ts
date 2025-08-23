import api from './api';
import { Watchlist, WatchlistCreate, WatchlistUpdate, WatchlistItem, WatchlistItemCreate } from '../types/watchlist';

export const getWatchlists = async (): Promise<Watchlist[]> => {
  const response = await api.get('/api/v1/watchlists/');
  return response.data;
};

export const createWatchlist = async (watchlist: WatchlistCreate): Promise<Watchlist> => {
  const response = await api.post('/api/v1/watchlists/', watchlist);
  return response.data;
};

export const updateWatchlist = async (id: string, watchlist: WatchlistUpdate): Promise<Watchlist> => {
  const response = await api.put(`/api/v1/watchlists/${id}`, watchlist);
  return response.data;
};

export const deleteWatchlist = async (id: string): Promise<void> => {
  await api.delete(`/api/v1/watchlists/${id}`);
};

export const addWatchlistItem = async (watchlistId: string, item: WatchlistItemCreate): Promise<WatchlistItem> => {
  const response = await api.post(`/api/v1/watchlists/${watchlistId}/items`, item);
  return response.data;
};

export const deleteWatchlistItem = async (watchlistId: string, itemId: string): Promise<void> => {
  await api.delete(`/api/v1/watchlists/${watchlistId}/items/${itemId}`);
};

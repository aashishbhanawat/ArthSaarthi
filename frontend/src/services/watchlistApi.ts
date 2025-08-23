import apiClient from './api';
import { Watchlist, WatchlistItem } from '../types/watchlist';

export const getWatchlists = async (): Promise<Watchlist[]> => {
    const response = await apiClient.get<Watchlist[]>('/api/v1/watchlists/');
    return response.data;
};

export const createWatchlist = async (name: string): Promise<Watchlist> => {
    const response = await apiClient.post<Watchlist>('/api/v1/watchlists/', { name });
    return response.data;
};

export const updateWatchlist = async (id: string, name: string): Promise<Watchlist> => {
    const response = await apiClient.put<Watchlist>(`/api/v1/watchlists/${id}`, { name });
    return response.data;
};

export const deleteWatchlist = async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/watchlists/${id}`);
};

export const addWatchlistItem = async (watchlistId: string, assetId: string): Promise<WatchlistItem> => {
    const response = await apiClient.post<WatchlistItem>(`/api/v1/watchlists/${watchlistId}/items`, { asset_id: assetId });
    return response.data;
};

export const removeWatchlistItem = async (watchlistId: string, itemId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/watchlists/${watchlistId}/items/${itemId}`);
};

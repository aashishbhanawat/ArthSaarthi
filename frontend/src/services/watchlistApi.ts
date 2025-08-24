import apiClient from './api';
import { Watchlist } from '../types/watchlist';

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

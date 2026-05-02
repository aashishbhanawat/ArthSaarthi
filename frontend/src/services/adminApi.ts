import apiClient from './api';
import { User, UserCreate, UserUpdate } from '../types/user';
import { HistoricalInterestRate, HistoricalInterestRateCreate, HistoricalInterestRateUpdate } from '../types/interestRate';

export const getUsers = async (): Promise<User[]> => {
  const response = await apiClient.get('/api/v1/users/');
  return response.data;
};

export const createUser = async (userData: UserCreate): Promise<User> => {
  const response = await apiClient.post('/api/v1/users/', userData);
  return response.data;
};

export const updateUser = async (
  userId: string,
  userData: UserUpdate
): Promise<User> => {
  const response = await apiClient.put(`/api/v1/users/${userId}`, userData);
  return response.data;
};

export const deleteUser = async (userId: string): Promise<User> => {
  const response = await apiClient.delete(`/api/v1/users/${userId}`);
  return response.data;
};

// --- Interest Rate Management (Admin) ---
export const getInterestRates = async (): Promise<HistoricalInterestRate[]> => {
  const response = await apiClient.get('/api/v1/admin/interest-rates/');
  return response.data;
};

export const createInterestRate = async (rateData: HistoricalInterestRateCreate): Promise<HistoricalInterestRate> => {
  const response = await apiClient.post('/api/v1/admin/interest-rates/', rateData);
  return response.data;
};

export const updateInterestRate = async (
  rateId: string,
  rateData: HistoricalInterestRateUpdate
): Promise<HistoricalInterestRate> => {
  const response = await apiClient.put(`/api/v1/admin/interest-rates/${rateId}`, rateData);
  return response.data;
};

export const deleteInterestRate = async (rateId: string): Promise<{ msg: string }> => {
  const response = await apiClient.delete(`/api/v1/admin/interest-rates/${rateId}`);
  return response.data;
};

// --- Asset Sync (Admin) ---
export interface AssetSyncResult {
  total_processed: number;
  newly_added: number;
  updated: number;
  timestamp: string;
}

export interface AssetSyncResponse {
  status: string;
  data: AssetSyncResult;
}

export const syncAssets = async (): Promise<AssetSyncResponse> => {
  const response = await apiClient.post('/api/v1/admin/assets/sync', {}, {
    timeout: 60000, // 60 second timeout for long-running sync
  });
  return response.data;
};

// --- Symbol Alias Management (Admin) ---
export interface AssetAliasWithAsset {
  id: string;
  alias_symbol: string;
  source: string;
  asset_id: string;
  asset_name: string;
  asset_ticker: string;
}

export interface AssetAliasCreate {
  alias_symbol: string;
  source: string;
  asset_id: string;
}

export interface AssetAliasUpdate {
  alias_symbol?: string;
  source?: string;
  asset_id?: string;
}

export interface AliasPageResponse {
  items: AssetAliasWithAsset[];
  total: number;
}

export const getAliases = async (params?: {
  q?: string;
  skip?: number;
  limit?: number;
}): Promise<AliasPageResponse> => {
  const response = await apiClient.get('/api/v1/admin/aliases/', { params });
  return response.data;
};

export const createAlias = async (data: AssetAliasCreate): Promise<AssetAliasWithAsset> => {
  const response = await apiClient.post('/api/v1/admin/aliases/', data);
  return response.data;
};

export const updateAlias = async (
  aliasId: string,
  data: AssetAliasUpdate
): Promise<AssetAliasWithAsset> => {
  const response = await apiClient.put(`/api/v1/admin/aliases/${aliasId}`, data);
  return response.data;
};

export const deleteAlias = async (aliasId: string): Promise<{ msg: string }> => {
  const response = await apiClient.delete(`/api/v1/admin/aliases/${aliasId}`);
  return response.data;
};

// --- FMV 2018 Management (Admin) ---
export interface FMVAsset {
  id: string;
  ticker_symbol: string;
  name: string;
  asset_type: string;
  isin?: string;
  fmv_2018: number | null;
}

export interface FMV2018BulkSeedResponse {
  status: string;
  updated: number;
  skipped: number;
  errors: number;
  message: string;
}

export const searchAssetsByFMV = async (query: string, limit = 50): Promise<FMVAsset[]> => {
  const response = await apiClient.get('/api/v1/admin/assets/fmv-search', {
    params: { query, limit },
  });
  return response.data;
};

export const updateFMV2018 = async (ticker: string, fmv_2018: number): Promise<FMVAsset> => {
  const response = await apiClient.patch(`/api/v1/admin/assets/${ticker}/fmv-2018`, { fmv_2018 });
  return response.data;
};

export const lookupFMV2018 = async (ticker: string): Promise<{ fmv_2018: number | null; message: string }> => {
  const response = await apiClient.get(`/api/v1/admin/assets/${ticker}/fmv-2018/lookup`);
  return response.data;
};

export const seedFMV2018 = async (overwrite: boolean): Promise<FMV2018BulkSeedResponse> => {
  const response = await apiClient.post('/api/v1/admin/assets/fmv-2018/seed', { overwrite }, {
    timeout: 120000, // 2 minute timeout for large BSE/AMFI downloads
  });
  return response.data;
};
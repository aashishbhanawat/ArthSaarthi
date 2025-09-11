import apiClient from './api';
import { Asset, MutualFundSearchResult } from '../types/asset';

export const searchMutualFunds = async (
  query: string
): Promise<MutualFundSearchResult[]> => {
  const response = await apiClient.get<MutualFundSearchResult[]>('/api/v1/assets/search-mf/', {
    params: { query: query.toLowerCase() },
  });
  return response.data;
};

export const checkPpfAccount = async (): Promise<Asset> => {
    const response = await apiClient.get<Asset>('/api/v1/assets/check-ppf');
    return response.data;
};

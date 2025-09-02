import apiClient from './api';
import { MutualFundSearchResult } from '../types/asset';

export const searchMutualFunds = async (
  query: string
): Promise<MutualFundSearchResult[]> => {
  const response = await apiClient.get<MutualFundSearchResult[]>('/api/v1/assets/search-mf/', {
    params: { query: query.toLowerCase() },
  });
  return response.data;
};

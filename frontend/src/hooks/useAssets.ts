import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { createAsset, searchStocks, getAssetsByType, AssetCreationPayload, AssetSearchResult } from '../services/portfolioApi';
import { searchMutualFunds } from '../services/assetApi';
import { Asset, MutualFundSearchResult } from '../types/asset';
import { useDebounce } from './useDebounce';

// Hook to search for assets using the unified search-stocks endpoint
export const useAssetSearch = (searchTerm: string) => {
  return useQuery<AssetSearchResult[], Error>({
    queryKey: ['assetSearch', searchTerm],
    queryFn: () => searchStocks(searchTerm),
    enabled: !!searchTerm, // Only run the query if there is a search term
  });
};

// Hook to create a new asset
export const useCreateAsset = () => {
  const queryClient = useQueryClient();
  return useMutation<Asset, Error, AssetCreationPayload>({
    mutationFn: (variables) => createAsset(variables),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assetSearch'] });
    },
  });
};

// Hook to search for mutual funds with debouncing
export const useMfSearch = (searchTerm: string) => {
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  return useQuery<MutualFundSearchResult[], Error>({
    queryKey: ['mfSearch', debouncedSearchTerm],
    queryFn: () => searchMutualFunds(debouncedSearchTerm),
    // Only run the query if the debounced term is long enough
    enabled: debouncedSearchTerm.length >= 3,
  });
};

// Hook to get assets of a specific type for a portfolio
export const useAssetsByType = (
  portfolioId: string,
  assetType: string,
  options: Omit<UseQueryOptions<Asset[], Error>, 'queryKey' | 'queryFn'> = {}
) => {
  return useQuery<Asset[], Error>({
    queryKey: ['assets', portfolioId, assetType],
    queryFn: () => getAssetsByType(portfolioId, assetType),
    ...options,
  });
};

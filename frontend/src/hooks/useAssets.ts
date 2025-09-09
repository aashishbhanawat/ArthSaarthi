import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createAsset, lookupAsset, AssetCreationPayload } from '../services/portfolioApi';
import { searchMutualFunds } from '../services/assetApi';
import { Asset, MutualFundSearchResult, PpfAccountCreate } from '../types/asset';
import { useDebounce } from './useDebounce';

// Hook to search for assets
export const useAssetSearch = (searchTerm: string) => {
  return useQuery<Asset[], Error>({
    queryKey: ['assetSearch', searchTerm],
    queryFn: () => lookupAsset(searchTerm),
    enabled: !!searchTerm, // Only run the query if there is a search term
  });
};

// Hook to create a new asset
export const useCreateAsset = () => {
  const queryClient = useQueryClient();
  return useMutation<Asset, Error, AssetCreationPayload | PpfAccountCreate>({
    mutationFn: (variables) => createAsset(variables),
    onSuccess: () => {
      // Invalidate queries that may be affected by a new asset
      queryClient.invalidateQueries({ queryKey: ['assetSearch'] });
      queryClient.invalidateQueries({ queryKey: ['portfolioHoldings'] });
      queryClient.invalidateQueries({ queryKey: ['portfolioSummary'] });
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

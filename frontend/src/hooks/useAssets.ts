import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createAsset, lookupAsset, AssetCreationPayload } from '../services/portfolioApi';
import { searchMutualFunds } from '../services/assetApi';
import { Asset, MutualFundSearchResult } from '../types/asset';
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

export const useCheckPpfAccount = () => {
    return useQuery<Asset, Error>({
        queryKey: ['checkPpfAccount'],
        queryFn: () => checkPpfAccount(),
        retry: (failureCount, error: { response?: { status?: number } }) => {
            if (error.response?.status === 404) {
                return false;
            }
            return failureCount < 3;
        },
    });
};

export const useCreatePpfAccountWithContribution = () => {
    const queryClient = useQueryClient();
    return useMutation<void, Error, PpfAccountCreateWithContribution>({
        mutationFn: (variables) => createPpfAccountWithContribution(variables),
        onSuccess: (data, variables) => {
            queryClient.invalidateQueries({ queryKey: ['portfolioHoldings', variables.portfolioId] });
            queryClient.invalidateQueries({ queryKey: ['portfolioSummary', variables.portfolioId] });
            queryClient.invalidateQueries({ queryKey: ['checkPpfAccount'] });
        },
    });
};

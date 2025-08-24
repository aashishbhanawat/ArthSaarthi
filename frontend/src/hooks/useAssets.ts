import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createAsset, lookupAsset } from '../services/portfolioApi';
import { Asset } from '../types/asset';

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
  return useMutation<Asset, Error, { ticker_symbol: string }>({
    mutationFn: (variables) => createAsset(variables.ticker_symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assetSearch'] });
    },
  });
};

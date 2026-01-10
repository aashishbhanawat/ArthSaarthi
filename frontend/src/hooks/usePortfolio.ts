import { useQuery } from '@tanstack/react-query';
import * as portfolioApi from '../services/portfolioApi';

export const usePortfolioAssets = (portfolioId: string) => {
    return useQuery({
        queryKey: ['portfolioAssets', portfolioId],
        queryFn: () => portfolioApi.getPortfolioAssets(portfolioId),
        enabled: !!portfolioId,
    });
};

export const useAssetSearch = (query: string, assetType?: string) => {
    return useQuery({
        queryKey: ['assetSearch', query, assetType],
        queryFn: () => portfolioApi.searchStocks(query, assetType),
        enabled: !!query, // Only run the query if there is a search term
    });
};

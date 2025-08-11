import { useQuery } from '@tanstack/react-query';
import * as portfolioApi from '../services/portfolioApi';

export const usePortfolioAssets = (portfolioId: string) => {
    return useQuery({
        queryKey: ['portfolioAssets', portfolioId],
        queryFn: () => portfolioApi.getPortfolioAssets(portfolioId),
        enabled: !!portfolioId,
    });
};

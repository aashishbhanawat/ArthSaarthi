import { useMutation, useQueryClient, QueryClient } from '@tanstack/react-query';
import * as portfolioApi from '../services/portfolioApi';

import { FixedDepositUpdate } from '../types/portfolio';

const invalidatePortfolioAndDashboardQueries = (queryClient: QueryClient, portfolioId: string) => {
    const queriesToInvalidate = [
        ['portfolio', portfolioId],
        ['dashboardSummary'],
        ['dashboardHistory'],
        ['dashboardAllocation'],
        ['portfolioAnalytics', portfolioId],
        ['portfolioSummary', portfolioId],
        ['portfolioHoldings', portfolioId],
        ['assetTransactions', portfolioId],
        ['assetAnalytics', portfolioId],
    ];
    queriesToInvalidate.forEach(queryKey => queryClient.invalidateQueries({ queryKey }));
};

export const useDeleteFixedDeposit = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId: _portfolioId, fdId }: { portfolioId: string; fdId: string }) =>
            portfolioApi.deleteFixedDeposit(fdId),
        onSuccess: (_, variables) => invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId),
    });
};

export const useUpdateFixedDeposit = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId: _portfolioId, fdId, data }: { portfolioId: string; fdId: string; data: FixedDepositUpdate }) =>
            portfolioApi.updateFixedDeposit(fdId, data),
        onSuccess: (_, variables) => invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId),
    });
};

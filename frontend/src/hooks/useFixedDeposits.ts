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
        mutationFn: ({ portfolioId, fdId }: { portfolioId: string; fdId: string }) => // eslint-disable-line @typescript-eslint/no-unused-vars
            portfolioApi.deleteFixedDeposit(fdId),
        onSuccess: (_, variables) => invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId),
    });
};

export const useUpdateFixedDeposit = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, fdId, data }: { portfolioId: string; fdId: string; data: FixedDepositUpdate }) => // eslint-disable-line @typescript-eslint/no-unused-vars
            portfolioApi.updateFixedDeposit(fdId, data),
        onSuccess: (_, variables) => invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId),
    });
};

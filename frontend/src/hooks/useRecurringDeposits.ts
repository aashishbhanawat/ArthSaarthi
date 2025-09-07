import { useMutation, useQuery, useQueryClient, QueryClient } from '@tanstack/react-query';
import * as portfolioApi from '../services/portfolioApi';
import { RecurringDepositCreate, RecurringDepositUpdate } from '../types/recurring_deposit';

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

export const useCreateRecurringDeposit = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: RecurringDepositCreate }) =>
            portfolioApi.createRecurringDeposit(portfolioId, data),
        onSuccess: (data) => {
            invalidatePortfolioAndDashboardQueries(queryClient, data.portfolio_id);
        },
    });
};

export const useUpdateRecurringDeposit = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ rdId, data }: { rdId: string; data: RecurringDepositUpdate }) =>
            portfolioApi.updateRecurringDeposit(rdId, data),
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['recurringDeposit', data.id] });
            invalidatePortfolioAndDashboardQueries(queryClient, data.portfolio_id);
        },
    });
};

export const useDeleteRecurringDeposit = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, rdId }: { portfolioId: string; rdId: string }) =>
            portfolioApi.deleteRecurringDeposit(rdId),
        onSuccess: (_, variables) => {
            invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId);
        },
    });
};

export const useRecurringDeposit = (rdId: string) => {
    return useQuery({
        queryKey: ['recurringDeposit', rdId],
        queryFn: () => portfolioApi.getRecurringDeposit(rdId),
        enabled: !!rdId,
    });
};

export const useRecurringDepositAnalytics = (rdId: string) => {
    return useQuery({
        queryKey: ['recurringDepositAnalytics', rdId],
        queryFn: () => portfolioApi.getRecurringDepositAnalytics(rdId),
        enabled: !!rdId,
    });
};

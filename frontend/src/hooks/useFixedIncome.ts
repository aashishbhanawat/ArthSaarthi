import { useMutation, useQueryClient, QueryClient } from '@tanstack/react-query';
import { createBond, createFixedDeposit, createPpf } from '../services/fixedIncomeApi';
import { BondCreate, FixedDepositCreate, PublicProvidentFundCreate } from '../types/fixed_income';

// Helper function to invalidate all queries related to portfolio and dashboard data
const invalidatePortfolioAndDashboardQueries = (queryClient: QueryClient, portfolioId: string) => {
    const queriesToInvalidate = [
        ['portfolio', portfolioId],
        ['dashboardSummary'],
        ['dashboardHistory'],
        ['dashboardAllocation'],
        ['portfolioAnalytics', portfolioId],
        ['portfolioSummary', portfolioId],
        ['portfolioHoldings', portfolioId],
        ['assetTransactions', portfolioId], // Invalidate all asset transactions for this portfolio
        ['assetAnalytics', portfolioId],    // Invalidate all asset analytics for this portfolio
    ];
    queriesToInvalidate.forEach(queryKey => queryClient.invalidateQueries({ queryKey: queryKey as any }));
};


export const useCreateFixedDeposit = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: FixedDepositCreate }) => createFixedDeposit(portfolioId, data),
        onSuccess: (_, variables) => {
            invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId);
        },
    });
};

export const useCreateBond = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: BondCreate }) => createBond(portfolioId, data),
        onSuccess: (_, variables) => {
            invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId);
        },
    });
};

export const useCreatePpf = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: PublicProvidentFundCreate }) => createPpf(portfolioId, data),
        onSuccess: (_, variables) => {
            invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId);
        },
    });
};

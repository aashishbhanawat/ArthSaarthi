import { useQuery, useMutation, useQueryClient, QueryClient } from '@tanstack/react-query';
import * as portfolioApi from '../services/portfolioApi';
import { PortfolioCreate, TransactionCreate, TransactionUpdate, TransactionsResponse } from '../types/portfolio';
import { HoldingsResponse, PortfolioSummary } from '../types/holding';
import { Asset } from '../types/asset';
import { PortfolioAnalytics } from '../types/analytics';

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
    queriesToInvalidate.forEach(queryKey => queryClient.invalidateQueries({ queryKey }));
};

export const usePortfolios = () => {
    return useQuery({
        queryKey: ['portfolios'],
        queryFn: portfolioApi.getPortfolios,
    });
};

export const usePortfolio = (id: string | undefined) => {
    return useQuery({
        queryKey: ['portfolio', id],
        // The '!' asserts that id is not undefined, which is safe because of the 'enabled' flag.
        queryFn: () => portfolioApi.getPortfolio(id!),
        enabled: !!id, // The query will not run if the id is undefined.
    });
};

export const useCreatePortfolio = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: PortfolioCreate) => portfolioApi.createPortfolio(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['portfolios'] });
        },
    });
};

export const useDeletePortfolio = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => portfolioApi.deletePortfolio(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['portfolios'] });
        },
    });
};

export const useCreateTransaction = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: TransactionCreate }) =>
            portfolioApi.createTransaction(portfolioId, data),
        onSuccess: (_, variables) => invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId),
    });
};

import { FixedDepositCreate } from '../types/portfolio';

export const useCreateFixedDeposit = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: FixedDepositCreate }) =>
            portfolioApi.createFixedDeposit(portfolioId, data),
        onSuccess: (_, variables) => invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId),
    });
};

export const usePortfolioAnalytics = (id: string | undefined) => {
    return useQuery<PortfolioAnalytics, Error>({
        queryKey: ['portfolioAnalytics', id],
        queryFn: () => portfolioApi.getPortfolioAnalytics(id!),
        enabled: !!id, // The query will not run if the id is undefined.
    });
};

export const useUpdateTransaction = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, transactionId, data }: { portfolioId: string; transactionId: string; data: TransactionUpdate }) =>
            portfolioApi.updateTransaction(portfolioId, transactionId, data),
        onSuccess: (_, variables) => invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId),
    });
};

export const useDeleteTransaction = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, transactionId }: { portfolioId: string; transactionId: string }) =>
            portfolioApi.deleteTransaction(portfolioId, transactionId),
        onSuccess: (_, variables) => invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId),
    });
};

export const usePortfolioSummary = (id: string | undefined) => {
    return useQuery<PortfolioSummary, Error>({
        queryKey: ['portfolioSummary', id],
        queryFn: () => portfolioApi.getPortfolioSummary(id!),
        enabled: !!id,
    });
};

export const usePortfolioHoldings = (id: string | undefined) => {
    return useQuery<HoldingsResponse, Error>({
        queryKey: ['portfolioHoldings', id],
        queryFn: () => portfolioApi.getPortfolioHoldings(id!),
        enabled: !!id,
    });
};

export const useAssetTransactions = (portfolioId: string | undefined, assetId: string | undefined) => {
    return useQuery({
        queryKey: ['assetTransactions', portfolioId, assetId],
        queryFn: () => portfolioApi.getAssetTransactions(portfolioId!, assetId!),
        enabled: !!portfolioId && !!assetId,
    });
};

export const useAssetAnalytics = (portfolioId: string, assetId: string, options: { enabled: boolean }) => {
  return useQuery<PortfolioAnalytics, Error>({
    queryKey: ['assetAnalytics', portfolioId, assetId],
    queryFn: () => portfolioApi.getAssetAnalytics(portfolioId, assetId),
    ...options,
  });
};

export const useTransactions = (
  portfolioId: string,
  filters: {
    asset_id?: string;
    transaction_type?: 'BUY' | 'SELL';
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  },
  enabled: boolean = true
) => {
  return useQuery<TransactionsResponse, Error>({
    queryKey: ['transactions', portfolioId, filters],
    queryFn: () => portfolioApi.getTransactions(portfolioId, filters),
    enabled: !!portfolioId && enabled,
    placeholderData: (previousData) => previousData,
  });
};

export const usePortfolioAssets = (portfolioId: string) => {
    return useQuery<Asset[], Error>({
        queryKey: ['portfolioAssets', portfolioId],
        queryFn: () => portfolioApi.getPortfolioAssets(portfolioId),
        enabled: !!portfolioId,
    });
};

export const useAssetSearch = (query: string) => {
    return useQuery<Asset[], Error>({
        queryKey: ['assetSearch', query],
        queryFn: () => portfolioApi.lookupAsset(query),
        enabled: !!query && query.length > 1,
    });
};
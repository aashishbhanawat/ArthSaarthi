import { useQuery, useMutation, useQueryClient, QueryClient } from '@tanstack/react-query';
import * as portfolioApi from '../services/portfolioApi';
import { BondCreate, BondUpdate } from '../types/bond';
import { PortfolioCreate, Transaction, TransactionCreate, TransactionUpdate, TransactionsResponse, FixedDepositCreate, PpfCreate } from '../types/portfolio';
import { RecurringDepositCreate } from '../types/recurring_deposit';
import { HoldingsResponse, PortfolioSummary } from '../types/holding';
import { Asset } from '../types/asset';
import { PortfolioAnalytics, AssetAnalytics, DiversificationResponse } from '../types/analytics';
import { useToast } from '../context/ToastContext';
import { ApiError, getErrorMessage } from '../types/api';

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
        ['diversification', portfolioId],    // Diversification charts
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
    const { showToast } = useToast();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: TransactionCreate }) =>
            portfolioApi.createTransaction(portfolioId, data),
        onSuccess: (_, variables) => {
            const { portfolioId, data } = variables;
            // The standard invalidation helper is great for most things.
            invalidatePortfolioAndDashboardQueries(queryClient, portfolioId);

            // However, corporate actions, especially splits, can have wide-ranging effects on historical
            // data that might not be caught by the standard dashboard/portfolio-level invalidations.
            // A stock split changes the quantity and cost basis of all previous transactions for an asset.
            // To be absolutely certain the UI reflects these deep changes, we will also specifically
            // invalidate the queries for the affected asset.
            const corporateActionTypes = ['SPLIT', 'BONUS', 'DIVIDEND'];
            if (data.asset_id && corporateActionTypes.includes(data.transaction_type)) {
                queryClient.invalidateQueries({ queryKey: ['assetTransactions', portfolioId, data.asset_id] });
                queryClient.invalidateQueries({ queryKey: ['assetAnalytics', portfolioId, data.asset_id] });
            }

            showToast('Transaction added successfully', 'success');
        },
        onError: (error: ApiError) => {
            showToast(`Error: ${getErrorMessage(error)}`, 'error');
        },
    });
};

export const useCreatePpfAccount = () => {
    const queryClient = useQueryClient();
    const { showToast } = useToast();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: PpfCreate }) =>
            portfolioApi.createPpfAccount(portfolioId, data),
        onSuccess: (_, variables) => {
            invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId);
            showToast('PPF account created successfully', 'success');
        },
        onError: (error: ApiError) => {
            showToast(`Error: ${getErrorMessage(error)}`, 'error');
        },
    });
};

export const useCreateFixedDeposit = () => {
    const queryClient = useQueryClient();
    const { showToast } = useToast();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: FixedDepositCreate }) =>
            portfolioApi.createFixedDeposit(portfolioId, data),
        onSuccess: (_, variables) => {
            invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId);
            showToast('Fixed Deposit created successfully', 'success');
        },
        onError: (error: ApiError) => {
            showToast(`Error: ${getErrorMessage(error)}`, 'error');
        },
    });
};

export const useCreateRecurringDeposit = () => {
    const queryClient = useQueryClient();
    const { showToast } = useToast();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: RecurringDepositCreate }) =>
            portfolioApi.createRecurringDeposit(portfolioId, data),
        onSuccess: (_, variables) => {
            invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId);
            showToast('Recurring Deposit created successfully', 'success');
        },
        onError: (error: ApiError) => {
            showToast(`Error: ${getErrorMessage(error)}`, 'error');
        },
    });
};

export const useCreateBond = () => {
    const queryClient = useQueryClient();
    const { showToast } = useToast();
    return useMutation({
        mutationFn: ({ portfolioId, bondData, transactionData }: { portfolioId: string; bondData: BondCreate, transactionData: TransactionCreate }) =>
            portfolioApi.createBond(portfolioId, bondData, transactionData),
        onSuccess: (_, variables) => {
            invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId);
            showToast('Bond added successfully', 'success');
        },
        onError: (error: ApiError) => {
            showToast(`Error: ${getErrorMessage(error)}`, 'error');
        },
    });
};

export const useUpdateBond = () => {
    const queryClient = useQueryClient();
    return useMutation({
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        mutationFn: ({ portfolioId: _portfolioId, bondId, data }: { portfolioId: string; bondId: string; data: BondUpdate }) =>
            portfolioApi.updateBond(bondId, data),
        onSuccess: (_, variables) => invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId),
    });
};

export const useDeleteBond = () => {
    const queryClient = useQueryClient();
    const { showToast } = useToast();
    return useMutation({
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        mutationFn: ({ portfolioId: _portfolioId, bondId }: { portfolioId: string; bondId: string }) => portfolioApi.deleteBond(bondId),
        onSuccess: (_, variables) => {
            invalidatePortfolioAndDashboardQueries(queryClient, variables.portfolioId);
            showToast('Bond deleted successfully', 'success');
        },
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

export const useAssetTransactions = (portfolioId?: string, assetId?: string) => {
    return useQuery<Transaction[], Error>({
        queryKey: ['assetTransactions', portfolioId, assetId],
        queryFn: () => portfolioApi.getAssetTransactions(portfolioId!, assetId!),
        enabled: !!portfolioId && !!assetId,
    });
};

export const useAssetAnalytics = (portfolioId?: string, assetId?: string) => {
    return useQuery<AssetAnalytics, Error>({
        queryKey: ['assetAnalytics', portfolioId, assetId],
        queryFn: () => portfolioApi.getAssetAnalytics(portfolioId!, assetId!),
        enabled: !!portfolioId && !!assetId,
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

export const usePortfolioAssets = (portfolioId: string, enabled: boolean = true) => {
    return useQuery<Asset[], Error>({
        queryKey: ['portfolioAssets', portfolioId],
        queryFn: () => portfolioApi.getPortfolioAssets(portfolioId),
        enabled: !!portfolioId && enabled,
    });
};

export const useAssetSearch = (query: string) => {
    return useQuery<Asset[], Error>({
        queryKey: ['assetSearch', query],
        queryFn: () => portfolioApi.lookupAsset(query),
        enabled: !!query && query.length > 1,
    });
};

export const useBenchmarkComparison = (portfolioId: string, benchmarkTicker: string) => {
    return useQuery({
        queryKey: ['benchmarkComparison', portfolioId, benchmarkTicker],
        queryFn: () => portfolioApi.getBenchmarkComparison(portfolioId, benchmarkTicker),
        enabled: !!portfolioId,
    });
};

export const useDiversification = (portfolioId: string | undefined) => {
    return useQuery<DiversificationResponse, Error>({
        queryKey: ['diversification', portfolioId],
        queryFn: () => portfolioApi.getDiversification(portfolioId!),
        enabled: !!portfolioId,
    });
};

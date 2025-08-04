import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as portfolioApi from '../services/portfolioApi';
import { PortfolioCreate, TransactionCreate } from '../types/portfolio';
import { Asset } from '../types/asset';
import { PortfolioAnalytics } from '../types/analytics';

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

export const useCreateAsset = () => {
    const queryClient = useQueryClient();
    return useMutation<Asset, Error, string>({
        mutationFn: (ticker: string) => portfolioApi.createAsset(ticker),
    });
};

export const useCreateTransaction = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ portfolioId, data }: { portfolioId: string; data: TransactionCreate }) =>
            portfolioApi.createTransaction(portfolioId, data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['portfolio', variables.portfolioId] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
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
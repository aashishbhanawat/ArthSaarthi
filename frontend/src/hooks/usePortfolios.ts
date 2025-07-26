import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as portfolioApi from '../services/portfolioApi';
import { PortfolioCreate, TransactionCreate } from '../types/portfolio';
import { Asset } from '../types/asset';

export const usePortfolios = () => {
    return useQuery({
        queryKey: ['portfolios'],
        queryFn: portfolioApi.getPortfolios,
    });
};

export const usePortfolio = (id: number) => {
    return useQuery({
        queryKey: ['portfolio', id],
        queryFn: () => portfolioApi.getPortfolio(id),
        enabled: !!id,
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
        mutationFn: (id: number) => portfolioApi.deletePortfolio(id),
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
        mutationFn: ({ portfolioId, data }: { portfolioId: number; data: TransactionCreate }) =>
            portfolioApi.createTransaction(portfolioId, data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['portfolio', variables.portfolioId] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        },
    });
};
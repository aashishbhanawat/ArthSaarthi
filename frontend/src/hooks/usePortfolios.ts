import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as portfolioApi from '../services/portfolioApi';
import { PortfolioCreate, TransactionCreate } from '../types/portfolio';

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
        enabled: !!id, // Only run query if id is truthy
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

export const useLookupAsset = () => {
    return useMutation({
        mutationFn: (ticker: string) => portfolioApi.lookupAsset(ticker),
    });
};

export const useCreateTransaction = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: TransactionCreate) => portfolioApi.createTransaction(data),
        onSuccess: (_data, variables) => {
            // Invalidate the specific portfolio query to refetch its details
            queryClient.invalidateQueries({ queryKey: ['portfolio', variables.portfolio_id] });
            queryClient.invalidateQueries({ queryKey: ['portfolios'] });
        },
    });
};
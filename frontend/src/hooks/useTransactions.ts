import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import {
  getTransactions,
  updateTransaction,
  deleteTransaction,
  TransactionFilters,
} from '../services/transactionApi';
import { TransactionsResponse, TransactionUpdate } from '../types/portfolio';

export const useTransactions = (filters: TransactionFilters) => {
  return useQuery<TransactionsResponse, Error>({
    queryKey: ['transactions', filters],
    queryFn: () => getTransactions(filters),
    placeholderData: keepPreviousData,
  });
};

export const useUpdateTransaction = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      portfolioId,
      transactionId,
      transactionData,
    }: {
      portfolioId: string;
      transactionId: string;
      transactionData: TransactionUpdate;
    }) => updateTransaction(portfolioId, transactionId, transactionData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
};

export const useDeleteTransaction = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      portfolioId,
      transactionId,
    }: {
      portfolioId: string;
      transactionId: string;
    }) => deleteTransaction(portfolioId, transactionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
};

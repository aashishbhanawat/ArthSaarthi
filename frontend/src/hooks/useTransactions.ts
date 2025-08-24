import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import {
  getTransactions,
  updateTransaction,
  deleteTransaction,
  TransactionFilters,
  TransactionUpdate,
} from '../services/transactionApi';
import { TransactionsResponse } from '../types/transaction';

export const useTransactions = (filters: TransactionFilters) => {
  console.log("useTransactions hook called with filters:", filters);
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

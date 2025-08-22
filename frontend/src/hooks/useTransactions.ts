import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTransactions,
  updateTransaction,
  deleteTransaction,
  TransactionFilters,
  TransactionUpdate,
} from '../services/transactionApi';

export const useTransactions = (filters: TransactionFilters) => {
  console.log("useTransactions hook called with filters:", filters);
  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => getTransactions(filters),
    keepPreviousData: true, // Keep showing old data while new data is fetching for a smoother UX
    onSuccess: (data) => {
      console.log("useTransactions data fetched:", data);
    },
    onError: (err) => console.log("useTransactions error:", err),
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


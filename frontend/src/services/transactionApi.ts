import apiClient from './api';
import { Transaction, TransactionsResponse, TransactionUpdate } from '../types/portfolio';

export interface TransactionFilters {
  portfolio_id?: string;
  asset_id?: string;
  transaction_type?: string;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
}

export const getTransactions = async (filters: TransactionFilters): Promise<TransactionsResponse> => {
  const { data } = await apiClient.get('/api/v1/transactions/', { params: filters });
  return data;
};

export const updateTransaction = async (
  portfolioId: string,
  transactionId: string,
  transactionData: TransactionUpdate
): Promise<Transaction> => {
  // The portfolio_id is required as a query parameter for the backend endpoint
  const { data } = await apiClient.put(
    `/api/v1/transactions/${transactionId}`,
    transactionData,
    { params: { portfolio_id: portfolioId } }
  );
  return data;
};

export const deleteTransaction = async (portfolioId: string, transactionId: string): Promise<void> => {
  // The portfolio_id is required as a query parameter for the backend endpoint
  await apiClient.delete(`/api/v1/transactions/${transactionId}`, {
    params: { portfolio_id: portfolioId },
  });
};

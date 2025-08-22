import apiClient from './api';
import { Transaction, TransactionsResponse } from '../types/transaction';

export interface TransactionFilters {
  portfolio_id?: string;
  asset_id?: string;
  transaction_type?: string;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
}

export interface TransactionUpdate {
  transaction_type?: 'BUY' | 'SELL';
  quantity?: number;
  price_per_unit?: number;
  transaction_date?: string; // YYYY-MM-DD
  fees?: number;
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
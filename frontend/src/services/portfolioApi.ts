import apiClient from './api';
import { Portfolio, Transaction, TransactionCreate, TransactionUpdate, PortfolioCreate, TransactionsResponse, FixedDepositCreate, FixedDeposit } from '../types/portfolio';
import { RecurringDeposit, RecurringDepositCreate, RecurringDepositUpdate, RecurringDepositDetails, RecurringDepositAnalytics } from '../types/recurring_deposit';
import { Asset } from '../types/asset';
import { HoldingsResponse, PortfolioSummary } from '../types/holding';
import { PortfolioAnalytics } from '../types/analytics';

export const getPortfolios = async (): Promise<Portfolio[]> => {
    const response = await apiClient.get<Portfolio[]>('/api/v1/portfolios/');
    return response.data;
};

export const getPortfolio = async (id: string): Promise<Portfolio> => {
    const response = await apiClient.get<Portfolio>(`/api/v1/portfolios/${id}`);
    return response.data;
};

export const createPortfolio = async (data: PortfolioCreate): Promise<Portfolio> => {
    const response = await apiClient.post<Portfolio>('/api/v1/portfolios/', data);
    return response.data;
};

export const deletePortfolio = async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/portfolios/${id}`);
};

export const lookupAsset = async (query: string): Promise<Asset[]> => {
    const response = await apiClient.get<Asset[]>('/api/v1/assets/lookup/', {
        params: { query },
    });
    return response.data;
};

export type AssetCreationPayload = {
    ticker_symbol: string;
    name: string;
    asset_type: 'STOCK' | 'MUTUAL_FUND' | 'CRYPTO' | 'OTHER';
    currency?: string;
    exchange?: string;
};

export const createAsset = async (payload: AssetCreationPayload): Promise<Asset> => {
    const response = await apiClient.post<Asset>('/api/v1/assets/', payload);
    return response.data;
};

export const getTransactions = async (
    portfolioId: string,
    filters: {
        asset_id?: string;
        transaction_type?: 'BUY' | 'SELL';
        start_date?: string;
        end_date?: string;
        skip?: number;
        limit?: number;
    }
): Promise<TransactionsResponse> => {
    const { data } = await apiClient.get<TransactionsResponse>(
        `/api/v1/portfolios/${portfolioId}/transactions/`,
        {
            params: filters,
        }
    );
    return data;
};

export const createTransaction = async (
    portfolioId: string,
    transactionData: TransactionCreate
): Promise<Transaction> => {
    const response = await apiClient.post<Transaction>(
        `/api/v1/portfolios/${portfolioId}/transactions/`,
        transactionData
    );
    return response.data;
};

export const createRecurringDeposit = async (
    portfolioId: string,
    rdData: RecurringDepositCreate
): Promise<RecurringDeposit> => {
    const response = await apiClient.post<RecurringDeposit>(
        `/api/v1/portfolios/${portfolioId}/recurring-deposits/`,
        rdData
    );
    return response.data;
};

export const getRecurringDeposit = async (
    rdId: string
): Promise<RecurringDepositDetails> => {
    const response = await apiClient.get<RecurringDepositDetails>(
        `/api/v1/recurring-deposits/${rdId}`
    );
    return response.data;
};

export const updateRecurringDeposit = async (
    rdId: string,
    rdData: RecurringDepositUpdate
): Promise<RecurringDeposit> => {
    const response = await apiClient.put<RecurringDeposit>(
        `/api/v1/recurring-deposits/${rdId}`,
        rdData
    );
    return response.data;
};

export const deleteRecurringDeposit = async (
    rdId: string
): Promise<void> => {
    await apiClient.delete(`/api/v1/recurring-deposits/${rdId}`);
};

export const getRecurringDepositAnalytics = async (
    rdId: string
): Promise<RecurringDepositAnalytics> => {
    const response = await apiClient.get<RecurringDepositAnalytics>(
        `/api/v1/recurring-deposits/${rdId}/analytics`
    );
    return response.data;
};

export const deleteFixedDeposit = async (
    portfolioId: string,
    fdId: string
): Promise<void> => {
    await apiClient.delete(`/api/v1/portfolios/${portfolioId}/fixed-deposits/${fdId}`);
};

export const updateFixedDeposit = async (
    portfolioId: string,
    fdId: string,
    fdData: FixedDepositUpdate
): Promise<FixedDeposit> => {
    const response = await apiClient.put<FixedDeposit>(
        `/api/v1/fixed-deposits/${fdId}`,
        fdData
    );
    return response.data;
};

export const createFixedDeposit = async (
    portfolioId: string,
    fdData: FixedDepositCreate
): Promise<FixedDeposit> => {
    const response = await apiClient.post<FixedDeposit>(
        `/api/v1/portfolios/${portfolioId}/fixed-deposits/`,
        fdData
    );
    return response.data;
};

export const updateTransaction = async (
    portfolioId: string,
    transactionId: string,
    transactionData: TransactionUpdate
): Promise<Transaction> => {
    const response = await apiClient.put<Transaction>(
        `/api/v1/portfolios/${portfolioId}/transactions/${transactionId}`,
        transactionData
    );
    return response.data;
};

export const deleteTransaction = async (
    portfolioId: string,
    transactionId: string
): Promise<void> => {
    await apiClient.delete(`/api/v1/portfolios/${portfolioId}/transactions/${transactionId}`);
};

export const getPortfolioAnalytics = async (id: string): Promise<PortfolioAnalytics> => {
    const response = await apiClient.get<PortfolioAnalytics>(`/api/v1/portfolios/${id}/analytics`);
    return response.data;
};

export const getPortfolioSummary = async (id: string): Promise<PortfolioSummary> => {
    const response = await apiClient.get<PortfolioSummary>(`/api/v1/portfolios/${id}/summary`);
    return response.data;
};

export const getPortfolioHoldings = async (id: string): Promise<HoldingsResponse> => {
    const response = await apiClient.get<HoldingsResponse>(`/api/v1/portfolios/${id}/holdings`);
    return response.data;
};

export const getAssetTransactions = async (
    portfolioId: string,
    assetId: string
): Promise<Transaction[]> => {
    const response = await apiClient.get<Transaction[]>(`/api/v1/portfolios/${portfolioId}/assets/${assetId}/transactions`);
    return response.data;
};

export const getAssetAnalytics = async (portfolioId: string, assetId: string): Promise<PortfolioAnalytics> => {
  const response = await apiClient.get(`/api/v1/portfolios/${portfolioId}/assets/${assetId}/analytics`);
  return response.data;
};

export const getPortfolioAssets = async (portfolioId: string): Promise<Asset[]> => {
    const response = await apiClient.get(`/api/v1/portfolios/${portfolioId}/assets`);
    return response.data;
};
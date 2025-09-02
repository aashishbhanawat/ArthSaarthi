import apiClient from './api';
import { Portfolio, Transaction, TransactionCreate, TransactionUpdate, PortfolioCreate, TransactionsResponse } from '../types/portfolio';
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
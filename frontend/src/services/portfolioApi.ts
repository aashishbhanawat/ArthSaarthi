import apiClient from './api';
import { Portfolio, PortfolioCreate, Transaction, TransactionCreate } from '../types/portfolio';
import { Asset } from '../types/asset';
import { PortfolioAnalytics } from '../types/analytics';

export const getPortfolios = async (): Promise<Portfolio[]> => {
    const response = await apiClient.get<Portfolio[]>('/api/v1/portfolios/');
    return response.data;
};

export const getPortfolio = async (id: number): Promise<Portfolio> => {
    const response = await apiClient.get<Portfolio>(`/api/v1/portfolios/${id}`);
    return response.data;
};

export const createPortfolio = async (data: PortfolioCreate): Promise<Portfolio> => {
    const response = await apiClient.post<Portfolio>('/api/v1/portfolios/', data);
    return response.data;
};

export const deletePortfolio = async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/portfolios/${id}`);
};

export const lookupAsset = async (query: string): Promise<Asset[]> => {
    const response = await apiClient.get<Asset[]>('/api/v1/assets/lookup/', {
        params: { query },
    });
    return response.data;
};

export const createAsset = async (ticker: string): Promise<Asset> => {
    const response = await apiClient.post<Asset>('/api/v1/assets/', {
        ticker_symbol: ticker,
    });
    return response.data;
};

export const createTransaction = async (
    portfolioId: number,
    transactionData: TransactionCreate
): Promise<Transaction> => {
    const response = await apiClient.post<Transaction>(
        `/api/v1/portfolios/${portfolioId}/transactions/`,
        transactionData
    );
    return response.data;
};

export const getPortfolioAnalytics = async (id: number): Promise<PortfolioAnalytics> => {
    const response = await apiClient.get<PortfolioAnalytics>(`/api/v1/portfolios/${id}/analytics`);
    return response.data;
};
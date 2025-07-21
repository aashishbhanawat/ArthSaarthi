import apiClient from './api';
import { Portfolio, PortfolioCreate, Transaction, TransactionCreate, Asset } from '../types/portfolio';

export const getPortfolios = async (): Promise<Portfolio[]> => {
    const response = await apiClient.get('/api/v1/portfolios/');
    return response.data;
};

export const getPortfolio = async (id: number): Promise<Portfolio> => {
    const response = await apiClient.get(`/api/v1/portfolios/${id}`);
    return response.data;
};

export const createPortfolio = async (data: PortfolioCreate): Promise<Portfolio> => {
    const response = await apiClient.post('/api/v1/portfolios/', data);
    return response.data;
};

export const deletePortfolio = async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/portfolios/${id}`);
};

export const lookupAsset = async (ticker: string): Promise<Asset> => {
    const response = await apiClient.get(`/api/v1/assets/lookup/${ticker}`);
    return response.data;
};

export const createTransaction = async (data: TransactionCreate): Promise<Transaction> => {
    const { portfolio_id, ...transactionData } = data;
    const response = await apiClient.post(`/api/v1/portfolios/${portfolio_id}/transactions/`, transactionData);
    return response.data;
};
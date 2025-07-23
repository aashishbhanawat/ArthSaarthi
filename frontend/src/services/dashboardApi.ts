import api from './api';
import {
    DashboardSummary,
    PortfolioHistoryResponse,
    AssetAllocationResponse,
} from '../types/dashboard';

export const getDashboardSummary = async (): Promise<DashboardSummary> => {
    const { data } = await api.get<DashboardSummary>('/api/v1/dashboard/summary');
    return data;
};

export const getDashboardHistory = async (
    range: string
): Promise<PortfolioHistoryResponse> => {
    const { data } = await api.get<PortfolioHistoryResponse>(
        '/api/v1/dashboard/history',
        { params: { range } }
    );
    return data;
};

export const getDashboardAllocation = async (): Promise<AssetAllocationResponse> => {
    const { data } = await api.get<AssetAllocationResponse>('/api/v1/dashboard/allocation');
    return data;
};
import api from './api';
import { DashboardSummary } from '../types/dashboard';

export const getDashboardSummary = async (): Promise<DashboardSummary> => {
    const { data } = await api.get<DashboardSummary>('/api/v1/dashboard/summary');
    return data;
};
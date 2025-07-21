import { useQuery } from '@tanstack/react-query';
import * as dashboardApi from '../services/dashboardApi';

export const useDashboardSummary = () => {
    return useQuery({
        queryKey: ['dashboardSummary'],
        queryFn: dashboardApi.getDashboardSummary,
    });
};
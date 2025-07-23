import { useQuery } from '@tanstack/react-query';
import * as dashboardApi from '../services/dashboardApi';

export const useDashboardSummary = () => {
    return useQuery({
        queryKey: ['dashboardSummary'],
        queryFn: dashboardApi.getDashboardSummary,
    });
};

export const useDashboardHistory = (range: string) => {
    return useQuery({
        queryKey: ['dashboardHistory', range],
        queryFn: () => dashboardApi.getDashboardHistory(range),
        enabled: !!range, // Only run the query if the range is provided
    });
};

export const useDashboardAllocation = () => {
    return useQuery({
        queryKey: ['dashboardAllocation'],
        queryFn: dashboardApi.getDashboardAllocation,
    });
};
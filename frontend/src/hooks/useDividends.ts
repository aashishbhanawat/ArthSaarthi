import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export interface DividendEntry {
    transaction_id: string;
    asset_name: string;
    asset_ticker: string;
    date: string;
    quantity: number;
    amount_native: number;
    currency: string;
    ttbr_date?: string | null;
    ttbr_rate?: number | null;
    amount_inr: number;
    period: string;
}

export interface DividendSummary {
    fy_year: string;
    entries: DividendEntry[];
    total_amount_inr: number;
    bucket_totals: Record<string, number>;
}

interface DividendsParams {
    fy: string;
    portfolio_id?: string;
}

export const useDividends = (params: DividendsParams) => {
    return useQuery<DividendSummary>({
        queryKey: ['dividends', params.fy, params.portfolio_id],
        queryFn: async () => {
            const queryParams = new URLSearchParams({
                fy: params.fy,
            });
            if (params.portfolio_id) {
                queryParams.append('portfolio_id', params.portfolio_id);
            }
            const response = await api.get(`/api/v1/dividends/?${queryParams.toString()}`);
            return response.data;
        },
        enabled: !!params.fy,
        staleTime: 0,
        gcTime: 0,
        refetchOnMount: 'always',
    });
};

import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export interface ScheduleFAEntry {
    country_code: string;
    country_name: string;
    entity_name: string;
    entity_address: string;
    zip_code: string;
    nature_of_entity: string;
    date_acquired: string | null;
    initial_value: number;
    peak_value: number;
    peak_value_date: string | null;
    closing_value: number;
    gross_amount_received: number;
    gross_proceeds_from_sale: number;
    currency: string;
    asset_ticker: string;
    quantity_held: number;
}

export interface ScheduleFASummary {
    calendar_year: number;
    assessment_year: string;
    entries: ScheduleFAEntry[];
    total_initial_value: number;
    total_peak_value: number;
    total_closing_value: number;
    total_gross_proceeds: number;
}

interface ScheduleFAParams {
    calendar_year: number;
    portfolio_id?: string;
}

export const useScheduleFA = (params: ScheduleFAParams) => {
    return useQuery<ScheduleFASummary>({
        queryKey: ['schedule-fa', params.calendar_year, params.portfolio_id],
        queryFn: async () => {
            const queryParams = new URLSearchParams({
                calendar_year: params.calendar_year.toString()
            });
            if (params.portfolio_id) {
                queryParams.append('portfolio_id', params.portfolio_id);
            }
            const response = await api.get(`/api/v1/schedule-fa/?${queryParams.toString()}`);
            return response.data;
        },
        enabled: !!params.calendar_year,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
};

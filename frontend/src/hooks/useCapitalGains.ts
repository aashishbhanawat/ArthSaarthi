import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export interface ITRPeriodValues {
    upto_15_6: number;
    upto_15_9: number;
    upto_15_12: number;
    upto_15_3: number;
    upto_31_3: number;
}

export interface ITRRow {
    category_label: string;
    period_values: ITRPeriodValues;
}

export interface GainEntry {
    transaction_id: string;
    asset_ticker: string;
    asset_name: string;
    asset_type: string;
    buy_date: string;
    sell_date: string;
    quantity: number;
    buy_price: number;
    sell_price: number;
    total_buy_value: number;
    total_sell_value: number;
    gain: number;
    gain_type: 'STCG' | 'LTCG';
    holding_days: number;
    tax_rate: string;
    is_grandfathered: boolean;
    corporate_action_adjusted: boolean;
    is_hybrid_warning: boolean;
}

export interface Schedule112AEntry {
    isin: string;
    asset_name: string;
    quantity: number;
    sale_price: number;
    full_value_consideration: number;
    cost_of_acquisition_orig: number;
    fmv_31jan2018: number | null;
    total_fmv: number | null;
    cost_of_acquisition_final: number;
    expenditure: number;
    total_deductions: number;
    balance: number;
    acquired_date: string;
    transfer_date: string;
}

export interface ForeignGainEntry {
    transaction_id: string;
    asset_ticker: string;
    asset_name: string;
    asset_type: string;
    currency: string;
    buy_date: string;
    sell_date: string;
    quantity: number;
    buy_price: number;
    sell_price: number;
    total_buy_value: number;
    total_sell_value: number;
    gain: number;
    gain_type: 'STCG' | 'LTCG';
    holding_days: number;
    country_code: string;
}

export interface CapitalGainsSummary {
    financial_year: string;
    total_stcg: number;
    total_ltcg: number;
    estimated_stcg_tax: number;
    estimated_ltcg_tax: number;
    itr_schedule_cg: ITRRow[];
    schedule_112a: Schedule112AEntry[];
    gains: GainEntry[];
    foreign_gains: ForeignGainEntry[];
}

interface CapitalGainsParams {
    fy: string;
    portfolio_id?: string;
    slab_rate: number;
}

export const useCapitalGains = (params: CapitalGainsParams) => {
    return useQuery<CapitalGainsSummary>({
        queryKey: ['capital-gains', params.fy, params.portfolio_id, params.slab_rate],
        queryFn: async () => {
            const queryParams = new URLSearchParams({
                fy: params.fy,
                slab_rate: params.slab_rate.toString()
            });
            if (params.portfolio_id) {
                queryParams.append('portfolio_id', params.portfolio_id);
            }
            const response = await api.get(`/api/v1/capital-gains/?${queryParams.toString()}`);
            return response.data;
        },
        enabled: !!params.fy,
        staleTime: 0,
        gcTime: 0,
        refetchOnMount: 'always',
    });
};

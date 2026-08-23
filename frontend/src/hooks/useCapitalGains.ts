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

export interface UnrealizedTaxLot {
    holding_id: string;
    asset_id: string;
    asset_ticker: string;
    asset_name: string;
    asset_type: string;
    buy_date: string;
    quantity: number;
    buy_price: number;
    current_price: number;
    total_cost: number;
    market_value: number;
    unrealized_gain: number;
    gain_type: 'STCG' | 'LTCG';
    holding_days: number;
    tax_rate: string;
    estimated_tax: number;
    is_grandfathered: boolean;
    is_foreign: boolean;
    currency: string;
}

export interface UnrealizedGainsSummary {
    financial_year: string;
    total_unrealized_stcg: number;
    total_unrealized_ltcg: number;
    total_unrealized_gain: number;
    section_112a_realized_used: number;
    section_112a_remaining_headroom: number;
    section_112a_unrealized_eligible: number;
    section_112a_unrealized_exemption_used: number;
    estimated_unrealized_stcg_tax: number;
    estimated_unrealized_ltcg_tax: number;
    total_estimated_tax: number;
    lots: UnrealizedTaxLot[];
}

export const useUnrealizedCapitalGains = (params: CapitalGainsParams) => {
    return useQuery<UnrealizedGainsSummary>({
        queryKey: ['unrealized-capital-gains', params.fy, params.portfolio_id, params.slab_rate],
        queryFn: async () => {
            const queryParams = new URLSearchParams({
                fy: params.fy,
                slab_rate: params.slab_rate.toString()
            });
            if (params.portfolio_id) {
                queryParams.append('portfolio_id', params.portfolio_id);
            }
            const response = await api.get(`/api/v1/capital-gains/unrealized?${queryParams.toString()}`);
            return response.data;
        },
        enabled: !!params.fy,
        staleTime: 0,
        gcTime: 0,
        refetchOnMount: 'always',
    });
};

export interface CapitalLossLedgerEntry {
    id: string;
    user_id: string;
    financial_year: string;
    assessment_year: string;
    stcl_amount: number;
    ltcl_amount: number;
    is_itr_filed_on_time: boolean;
    notes?: string;
    years_remaining: number;
    is_expired: boolean;
}

export interface CapitalLossLedgerCreate {
    financial_year: string;
    assessment_year: string;
    stcl_amount: number;
    ltcl_amount: number;
    is_itr_filed_on_time: boolean;
    notes?: string;
}

export interface SetOffBreakdown {
    gross_stcg: number;
    gross_stcl: number;
    gross_ltcg: number;
    gross_ltcl: number;
    cy_stcl_offset_against_stcg: number;
    cy_stcl_offset_against_ltcg: number;
    cy_ltcl_offset_against_ltcg: number;
    bf_stcl_used: number;
    bf_ltcl_used: number;
    net_taxable_stcg: number;
    net_taxable_ltcg: number;
    unabsorbed_stcl_to_carry_forward: number;
    unabsorbed_ltcl_to_carry_forward: number;
    gross_estimated_tax: number;
    net_estimated_tax: number;
    tax_saved_via_setoff: number;
}

export interface CapitalSetOffSummary {
    financial_year: string;
    assessment_year: string;
    breakdown: SetOffBreakdown;
    loss_ledger_entries: CapitalLossLedgerEntry[];
}

export interface TaxLossHarvestingItem {
    holding_id: string;
    asset_id: string;
    asset_ticker: string;
    asset_name: string;
    asset_type: string;
    buy_date: string;
    quantity: number;
    buy_price: number;
    current_price: number;
    total_cost: number;
    market_value: number;
    unrealized_loss: number;
    loss_type: 'STCL' | 'LTCL';
    holding_days: number;
    potential_tax_saved: number;
    recommended_sell_quantity: number;
    recommendation_reason: string;
}

export interface TaxLossHarvestingSummary {
    financial_year: string;
    total_harvestable_stcl: number;
    total_harvestable_ltcl: number;
    total_potential_tax_savings: number;
    net_taxable_stcg_before_harvesting: number;
    net_taxable_ltcg_before_harvesting: number;
    harvesting_opportunities: TaxLossHarvestingItem[];
}

export const useCapitalSetOff = (params: CapitalGainsParams) => {
    return useQuery<CapitalSetOffSummary>({
        queryKey: ['capital-setoff', params.fy, params.portfolio_id, params.slab_rate],
        queryFn: async () => {
            const queryParams = new URLSearchParams({
                fy: params.fy,
                slab_rate: params.slab_rate.toString()
            });
            if (params.portfolio_id) {
                queryParams.append('portfolio_id', params.portfolio_id);
            }
            const response = await api.get(`/api/v1/capital-gains/set-off?${queryParams.toString()}`);
            return response.data;
        },
        enabled: !!params.fy,
        staleTime: 0,
        gcTime: 0,
        refetchOnMount: 'always',
    });
};

export const useCapitalLossLedger = (fy: string = '2025-26') => {
    return useQuery<CapitalLossLedgerEntry[]>({
        queryKey: ['loss-ledger', fy],
        queryFn: async () => {
            const response = await api.get(`/api/v1/capital-gains/loss-ledger?fy=${fy}`);
            return response.data;
        },
        staleTime: 0,
        gcTime: 0,
        refetchOnMount: 'always',
    });
};

export const useTaxLossHarvesting = (params: CapitalGainsParams) => {
    return useQuery<TaxLossHarvestingSummary>({
        queryKey: ['tax-loss-harvesting', params.fy, params.portfolio_id, params.slab_rate],
        queryFn: async () => {
            const queryParams = new URLSearchParams({
                fy: params.fy,
                slab_rate: params.slab_rate.toString()
            });
            if (params.portfolio_id) {
                queryParams.append('portfolio_id', params.portfolio_id);
            }
            const response = await api.get(`/api/v1/capital-gains/tax-loss-harvesting?${queryParams.toString()}`);
            return response.data;
        },
        enabled: !!params.fy,
        staleTime: 0,
        gcTime: 0,
        refetchOnMount: 'always',
    });
};



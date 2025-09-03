export interface Holding {
    asset_id: string;
    ticker_symbol: string;
    asset_name: string;
    asset_type: string;
    quantity: number;
    average_buy_price: number;
    total_invested_amount: number;
    current_price: number;
    current_value: number;
    days_pnl: number;
    days_pnl_percentage: number;
    unrealized_pnl: number;
    unrealized_pnl_percentage: number;

    // Optional fields for Fixed Deposits
    institution_name?: string;
    account_number?: string;
    principal_amount?: number;
    interest_rate?: number;
    start_date?: string;
    maturity_date?: string;
    payout_type?: 'REINVESTMENT' | 'PAYOUT';
    compounding_frequency?: 'MONTHLY' | 'QUARTERLY' | 'HALF_YEARLY' | 'ANNUALLY' | 'AT_MATURITY';

    // Optional fields for Bonds
    isin?: string;
    face_value?: number;
    coupon_rate?: number;
    purchase_price?: number;
    purchase_date?: string;
    interest_payout_frequency?: 'ANNUALLY' | 'SEMI_ANNUALLY';

    // Optional fields for PPF
    opening_date?: string;
}

export interface HoldingsResponse {
    holdings: Holding[];
}

export interface PortfolioSummary {
    total_value: number;
    total_invested_amount: number;
    days_pnl: number;
    total_unrealized_pnl: number;
    total_realized_pnl: number;
}
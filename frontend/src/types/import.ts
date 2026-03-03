import { Portfolio } from './portfolio';
import { User } from './user';

export interface ImportSession {
    id: string;
    user_id: string;
    portfolio_id: string;
    file_name: string;
    file_path: string;
    source: string;
    parsed_file_path: string | null;
    status: 'PENDING' | 'PARSING' | 'PARSED' | 'COMMITTING' | 'COMPLETED' | 'FAILED';
    error_message: string | null;
    created_at: string;
    updated_at: string;
    user: User;
    portfolio: Portfolio;
}

export interface ParsedTransaction {
    transaction_date: string;
    ticker_symbol: string;
    transaction_type: 'BUY' | 'SELL';
    quantity: number;
    price_per_unit: number;
    fees: number;
}

export interface AssetAliasCreate {
    asset_id: string;
    alias_symbol: string;
    source: string;
}

export interface ImportSessionPreview {
    valid_new: ParsedTransaction[];
    duplicates: ParsedTransaction[];
    invalid: { row_data: Record<string, unknown>; error: string }[];
    needs_mapping: ParsedTransaction[];
}

export interface ImportSessionCommit {
    transactions_to_commit: ParsedTransaction[];
    aliases_to_create: AssetAliasCreate[];
}

export interface ParsedFixedDeposit {
    bank: string;
    account_number: string;
    principal_amount: number;
    interest_rate: number;
    start_date: string;
    maturity_date: string;
    maturity_amount: number;
    interest_payout: 'Payout' | 'Cumulative';
    compounding_frequency: 'Monthly' | 'Quarterly' | 'Half-Yearly' | 'Yearly';
}

export interface FDImportPreview {
    parsed_fds: ParsedFixedDeposit[];
    duplicates: ParsedFixedDeposit[];
}

export interface FDImportCommit {
    fds_to_commit: ParsedFixedDeposit[];
}
import { Portfolio } from './portfolio';
import { User } from './user';

export interface ImportSession {
    id: string;
    user_id: string;
    portfolio_id: string;
    file_name: string;
    file_path: string;
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
}

export interface ImportSessionCommit {
    transactions_to_commit: ParsedTransaction[];
    aliases_to_create: AssetAliasCreate[];
}
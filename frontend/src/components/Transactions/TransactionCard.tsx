import React from 'react';
import { Transaction } from '../../types/portfolio';
import { usePrivacySensitiveCurrency, formatDate } from '../../utils/formatting';
import { InformationCircleIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline';

interface TransactionCardProps {
    transaction: Transaction;
    onEdit: (transaction: Transaction) => void;
    onDelete: (transaction: Transaction) => void;
    onViewDetails: (transaction: Transaction) => void;
}

const getTypeBadgeClasses = (type: string) => {
    switch (type) {
        case 'BUY': return 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/40';
        case 'SELL': return 'text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/40';
        case 'RSU_VEST': return 'text-purple-700 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/40';
        case 'ESPP_PURCHASE': return 'text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/40';
        case 'DIVIDEND': return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/40';
        case 'SPLIT': return 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/40';
        case 'BONUS': return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/40';
        case 'FD_DEPOSIT': return 'text-teal-700 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/40';
        case 'FD_MATURITY': return 'text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/40';
        default: return 'text-gray-700 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/40';
    }
};

const getTypeLabel = (type: string) => {
    switch (type) {
        case 'FD_DEPOSIT': return 'FD Deposit';
        case 'FD_MATURITY': return 'FD Maturity';
        default: return type;
    }
};

const hasUserVisibleDetails = (details: Record<string, unknown> | null | undefined): boolean => {
    if (!details) return false;
    const internalKeys = new Set(['_fd_id']);
    return Object.keys(details).some(k => !internalKeys.has(k));
};

const isSyntheticFd = (tx: Transaction): boolean =>
    !!(tx.details as Record<string, unknown> | null)?._fd_id;

const TransactionCard: React.FC<TransactionCardProps> = ({ transaction: tx, onEdit, onDelete, onViewDetails }) => {
    const formatCurrency = usePrivacySensitiveCurrency();
    const value = Number(tx.price_per_unit) * Number(tx.quantity) * (Number(tx.details?.fx_rate) || 1);

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-3 transition-all hover:shadow-md">
            <div className="flex justify-between items-start mb-3">
                <div className="flex flex-col max-w-[70%]">
                    <span className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">{formatDate(tx.transaction_date)}</span>
                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100 mt-0.5 truncate">{tx.asset.name}</span>
                    <span className="text-[11px] font-mono text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 px-1.5 rounded w-fit mt-1">
                        {tx.asset.ticker_symbol}
                    </span>
                </div>
                <div className="flex flex-col items-end">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${getTypeBadgeClasses(tx.transaction_type)}`}>
                        {getTypeLabel(tx.transaction_type)}
                    </span>
                    {hasUserVisibleDetails(tx.details as Record<string, unknown> | null) && (
                        <button
                            onClick={() => onViewDetails(tx)}
                            className="text-blue-500 hover:text-blue-700 mt-2 flex items-center gap-1 text-[10px] font-medium"
                        >
                            <InformationCircleIcon className="h-4 w-4" />
                            Details
                        </button>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 py-3 border-t border-gray-50 dark:border-gray-700">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Quantity</span>
                    <span className="text-sm font-semibold dark:text-gray-200">
                        {Number(tx.quantity).toLocaleString('en-IN', { maximumFractionDigits: tx.asset.asset_type === 'FIXED_DEPOSIT' ? 0 : 4 })}
                    </span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Price</span>
                    <span className="text-sm font-semibold dark:text-gray-200">{formatCurrency(tx.price_per_unit, tx.asset.currency)}</span>
                </div>
            </div>

            <div className="pt-3 border-t border-gray-50 dark:border-gray-700 flex justify-between items-center">
                <div className="flex items-center gap-1">
                    {!isSyntheticFd(tx) && (
                        <button
                            onClick={() => onEdit(tx)}
                            className="p-2 text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                            aria-label="Edit transaction"
                        >
                            <PencilIcon className="h-5 w-5" />
                        </button>
                    )}
                    {(!isSyntheticFd(tx) || tx.transaction_type === 'FD_MATURITY') && (
                        <button
                            onClick={() => onDelete(tx)}
                            className="p-2 text-gray-500 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                            aria-label="Delete transaction"
                        >
                            <TrashIcon className="h-5 w-5" />
                        </button>
                    )}
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Total Value (INR)</span>
                    <span className="text-base font-extrabold text-blue-600 dark:text-blue-400">
                        {formatCurrency(value, 'INR')}
                    </span>
                </div>
            </div>
        </div>
    );
};

export default TransactionCard;

import React, { useState } from 'react';
import { Transaction } from '../../types/portfolio';
import { TransactionType } from '../../types/enums';
import { usePrivacySensitiveCurrency, formatDate } from '../../utils/formatting';
import TransactionDetailsModal from './TransactionDetailsModal';
import TransactionCard from './TransactionCard';
import { InformationCircleIcon } from '@heroicons/react/24/outline';

interface TransactionHistoryTableProps {
    transactions: Transaction[];
    onEdit: (transaction: Transaction) => void;
    onDelete: (transaction: Transaction) => void;
}

const getTypeColor = (type: string) => {
    switch (type) {
        case 'BUY': return 'text-green-600';
        case 'SELL': return 'text-red-600';
        case 'RSU_VEST': return 'text-purple-600';
        case 'ESPP_PURCHASE': return 'text-blue-600';
        case 'DIVIDEND': return 'text-green-500';
        case 'SPLIT': return 'text-orange-500';
        case 'BONUS': return 'text-green-500';
        case 'FD_DEPOSIT': return 'text-teal-600';
        case 'FD_MATURITY': return 'text-amber-600';
        default: return 'text-gray-600';
    }
};

const getTypeLabel = (type: string) => {
    switch (type) {
        case 'FD_DEPOSIT': return 'FD Deposit';
        case 'FD_MATURITY': return 'FD Maturity';
        default: return type;
    }
};

/** Returns true if details has keys that are meaningful to show to the user */
const hasUserVisibleDetails = (details: Record<string, unknown> | null | undefined): boolean => {
    if (!details) return false;
    const internalKeys = new Set(['_fd_id']);
    return Object.keys(details).some(k => !internalKeys.has(k));
};

const isSyntheticFd = (tx: Transaction): boolean =>
    !!(tx.details as Record<string, unknown> | null)?._fd_id;

const TransactionHistoryTable: React.FC<TransactionHistoryTableProps> = ({ transactions, onEdit, onDelete }) => {
    const formatCurrency = usePrivacySensitiveCurrency();
    const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);

    if (transactions.length === 0) {
        return <div className="text-center p-8 text-gray-500 card">No transactions found for the selected filters.</div>;
    }

    return (
        <>
            <div className="md:hidden space-y-3">
                {transactions.map(tx => (
                    <TransactionCard
                        key={tx.id}
                        transaction={tx}
                        onEdit={onEdit}
                        onDelete={onDelete}
                        onViewDetails={setSelectedTransaction}
                    />
                ))}
            </div>

            <div className="hidden md:block table-container shadow-none lg:shadow-sm">
                <table className="table-auto w-full">
                    <thead className="bg-gray-100 dark:bg-gray-800">
                        <tr>
                            <th className="p-3 text-left text-sm font-semibold text-gray-600 dark:text-gray-400 whitespace-nowrap">Date</th>
                            <th className="p-3 text-left text-sm font-semibold text-gray-600 dark:text-gray-400 whitespace-nowrap">Ticker</th>
                            <th className="p-3 text-left text-sm font-semibold text-gray-600 dark:text-gray-400 whitespace-nowrap">Asset</th>
                            <th className="p-3 text-left text-sm font-semibold text-gray-600 dark:text-gray-400 whitespace-nowrap">Type</th>
                            <th className="p-3 text-right text-sm font-semibold text-gray-600 dark:text-gray-400 whitespace-nowrap">Qty</th>
                            <th className="p-3 text-right text-sm font-semibold text-gray-600 dark:text-gray-400 whitespace-nowrap">Price</th>
                            <th className="p-3 text-right text-sm font-semibold text-gray-600 dark:text-gray-400 whitespace-nowrap">Value (INR)</th>
                            <th className="p-3 text-center text-sm font-semibold text-gray-600 dark:text-gray-400 whitespace-nowrap">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {transactions.map((tx) => (
                            <tr key={tx.id} className="border-b hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700/50">
                                <td className="p-3 text-sm whitespace-nowrap">{formatDate(tx.transaction_date)}</td>
                                <td className="p-3 text-sm font-mono whitespace-nowrap">{tx.asset.ticker_symbol}</td>
                                <td className="p-3 text-sm min-w-[120px]">{tx.asset.name}</td>
                                <td className={`p-3 text-sm font-semibold whitespace-nowrap ${getTypeColor(tx.transaction_type)}`}>
                                    {getTypeLabel(tx.transaction_type)}
                                    {hasUserVisibleDetails(tx.details as Record<string, unknown> | null) && (
                                        <button
                                            className="ml-1 text-blue-500 hover:text-blue-700 align-middle focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded-full"
                                            onClick={() => setSelectedTransaction(tx)}
                                            title="View Details"
                                            aria-label="View details"
                                        >
                                            <InformationCircleIcon className="h-5 w-5" />
                                        </button>
                                    )}
                                </td>
                                <td className="p-3 text-sm text-right whitespace-nowrap">{Number(tx.quantity).toLocaleString('en-IN', { maximumFractionDigits: tx.asset.asset_type === 'FIXED_DEPOSIT' ? 0 : 4 })}</td>
                                <td className="p-3 text-sm text-right whitespace-nowrap">{formatCurrency(tx.price_per_unit, tx.asset.currency)}</td>
                                <td className="p-3 text-sm text-right whitespace-nowrap">{formatCurrency(
                                    Number(tx.price_per_unit) * Number(tx.quantity) * (Number(tx.details?.fx_rate) || 1),
                                    'INR'
                                )}</td>
                                <td className="p-3 text-center">
                                    <div className="flex justify-center space-x-2">
                                        {!isSyntheticFd(tx) && (
                                            <button onClick={() => onEdit(tx)} className="btn btn-secondary btn-xs" aria-label={`Edit ${tx.transaction_type} transaction for ${tx.asset.ticker_symbol}`}>Edit</button>
                                        )}
                                        {(!isSyntheticFd(tx) || tx.transaction_type === TransactionType.FD_MATURITY) && (
                                            <button onClick={() => onDelete(tx)} className="btn btn-danger btn-xs" aria-label={`Delete ${tx.transaction_type} transaction for ${tx.asset.ticker_symbol}`}>Delete</button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {selectedTransaction && (
                <TransactionDetailsModal
                    transaction={selectedTransaction}
                    onClose={() => setSelectedTransaction(null)}
                />
            )}
        </>
    );
};

export default TransactionHistoryTable;

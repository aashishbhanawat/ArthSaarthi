import React, { useState } from 'react';
import { Transaction } from '../../types/portfolio';
import { TransactionType } from '../../types/enums';
import { usePrivacySensitiveCurrency, formatDate } from '../../utils/formatting';
import TransactionDetailsModal from './TransactionDetailsModal';
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
            <div className="card overflow-x-auto">
                <table className="table-auto w-full">
                    <thead className="bg-gray-100">
                        <tr>
                            <th className="p-3 text-left text-sm font-semibold text-gray-600">Date</th>
                            <th className="p-3 text-left text-sm font-semibold text-gray-600">Ticker</th>
                            <th className="p-3 text-left text-sm font-semibold text-gray-600">Asset Name</th>
                            <th className="p-3 text-left text-sm font-semibold text-gray-600">Type</th>
                            <th className="p-3 text-right text-sm font-semibold text-gray-600">Quantity</th>
                            <th className="p-3 text-right text-sm font-semibold text-gray-600">Price/Unit</th>
                            <th className="p-3 text-right text-sm font-semibold text-gray-600">Total Value (INR)</th>
                            <th className="p-3 text-center text-sm font-semibold text-gray-600">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {transactions.map((tx) => (
                            <tr key={tx.id} className="border-b hover:bg-gray-50">
                                <td className="p-3 text-sm">{formatDate(tx.transaction_date)}</td>
                                <td className="p-3 text-sm font-mono">{tx.asset.ticker_symbol}</td>
                                <td className="p-3 text-sm">{tx.asset.name}</td>
                                <td className={`p-3 text-sm font-semibold ${getTypeColor(tx.transaction_type)}`}>
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
                                <td className="p-3 text-sm text-right">{Number(tx.quantity).toLocaleString('en-IN', { maximumFractionDigits: tx.asset.asset_type === 'FIXED_DEPOSIT' ? 0 : 4 })}</td>
                                <td className="p-3 text-sm text-right">{formatCurrency(tx.price_per_unit, tx.asset.currency)}</td>
                                <td className="p-3 text-sm text-right">{formatCurrency(
                                    Number(tx.price_per_unit) * Number(tx.quantity) * (Number(tx.details?.fx_rate) || 1),
                                    'INR'
                                )}</td>
                                <td className="p-3 text-center">
                                    <div className="flex justify-center space-x-2">
                                        {!isSyntheticFd(tx) && (
                                            <button onClick={() => onEdit(tx)} className="btn btn-secondary btn-sm" aria-label={`Edit ${tx.transaction_type} transaction for ${tx.asset.ticker_symbol}`}>Edit</button>
                                        )}
                                        {(!isSyntheticFd(tx) || tx.transaction_type === TransactionType.FD_MATURITY) && (
                                            <button onClick={() => onDelete(tx)} className="btn btn-danger btn-sm" aria-label={`Delete ${tx.transaction_type} transaction for ${tx.asset.ticker_symbol}`}>Delete</button>
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

import React from 'react';
import { Transaction } from '../../types/portfolio';
import { usePrivacySensitiveCurrency, formatDate } from '../../utils/formatting';

interface TransactionDetailsModalProps {
    transaction: Transaction;
    onClose: () => void;
}

const TransactionDetailsModal: React.FC<TransactionDetailsModalProps> = ({ transaction, onClose }) => {
    const formatCurrency = usePrivacySensitiveCurrency();

    const formatDetailValue = (key: string, value: unknown): string => {
        if (typeof value === 'object' && value !== null) {
            return JSON.stringify(value);
        }
        if (key === 'fmv' || key === 'price_per_unit') {
            return formatCurrency(Number(value), transaction.asset.currency);
        }
        if (key === 'fx_rate') {
            return Number(value).toFixed(4);
        }
        return String(value);
    };

    const formatDetailKey = (key: string): string => {
        return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    };

    return (
        <div className="modal-overlay z-40" onClick={onClose}>
            <div role="dialog" aria-modal="true" className="modal-content w-11/12 md:w-1/2 lg:w-1/3 p-6" onClick={e => e.stopPropagation()}>
                <h2 className="text-xl font-bold mb-4">Transaction Details</h2>

                <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="font-semibold text-gray-600">Type</div>
                        <div>{transaction.transaction_type}</div>

                        <div className="font-semibold text-gray-600">Asset</div>
                        <div>{transaction.asset.name} ({transaction.asset.ticker_symbol})</div>

                        <div className="font-semibold text-gray-600">Date</div>
                        <div>{formatDate(transaction.transaction_date)}</div>
                    </div>

                    {transaction.details && Object.keys(transaction.details).length > 0 ? (
                        <div className="border-t pt-4">
                            <h3 className="font-semibold mb-2 text-gray-700">Additional Information</h3>
                            <div className="bg-gray-50 rounded p-3">
                                {Object.entries(transaction.details).map(([key, value]) => (
                                    <div key={key} className="grid grid-cols-2 gap-2 text-sm py-1 border-b border-gray-100 last:border-0">
                                        <div className="text-gray-600">{formatDetailKey(key)}</div>
                                        <div className="font-mono text-gray-800 break-all whitespace-pre-wrap">{formatDetailValue(key, value)}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <p className="text-gray-500 italic">No additional details available.</p>
                    )}
                </div>

                <div className="flex justify-end mt-6">
                    <button onClick={onClose} className="btn btn-secondary">Close</button>
                </div>
            </div>
        </div>
    );
};

export default TransactionDetailsModal;

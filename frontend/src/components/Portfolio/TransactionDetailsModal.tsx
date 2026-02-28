import React from 'react';
import { Transaction } from '../../types/portfolio';
import { formatCurrency, formatDate } from '../../utils/formatting';

interface TransactionDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    transaction: Transaction | null;
}

const TransactionDetailsModal: React.FC<TransactionDetailsModalProps> = ({ isOpen, onClose, transaction }) => {
    if (!isOpen || !transaction) return null;

    const details = transaction.details || {};
    const hasDetails = Object.keys(details).length > 0;
    const isForeign = transaction.asset.currency !== 'INR';

    return (
        <div className="modal-overlay z-40" onClick={onClose}>
            <div className="modal-content w-11/12 max-w-lg p-6 relative" onClick={e => e.stopPropagation()}>
                <button onClick={onClose} aria-label="Close" className="absolute right-4 top-4 text-gray-500 hover:text-gray-700">
                    &times;
                </button>
                <h2 className="text-xl font-bold mb-4">Transaction Details</h2>

                <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span className="block text-gray-500">Asset</span>
                            <span className="font-semibold text-gray-800">{transaction.asset.name}</span>
                        </div>
                        <div>
                            <span className="block text-gray-500">Date</span>
                            <span className="font-semibold text-gray-800">{formatDate(transaction.transaction_date)}</span>
                        </div>
                        <div>
                            <span className="block text-gray-500">Type</span>
                            <span className="font-semibold text-gray-800">{transaction.transaction_type}</span>
                        </div>
                        <div>
                            <span className="block text-gray-500">Quantity</span>
                            <span className="font-semibold text-gray-800">{transaction.quantity}</span>
                        </div>
                        <div>
                            <span className="block text-gray-500">Price</span>
                            <span className="font-semibold text-gray-800">{formatCurrency(transaction.price_per_unit, transaction.asset.currency)}</span>
                        </div>
                        <div>
                            <span className="block text-gray-500">Total Value</span>
                            <span className="font-semibold text-gray-800">{formatCurrency(Number(transaction.price_per_unit) * Number(transaction.quantity), transaction.asset.currency)}</span>
                        </div>
                    </div>

                    <div className="border-t border-gray-200 my-4"></div>

                    {/* Foreign Transaction Details */}
                    {isForeign && (
                        <div className="bg-blue-50 p-3 rounded-md mb-4 border border-blue-100">
                            <h3 className="text-sm font-bold text-blue-800 mb-2">Foreign Exchange Details</h3>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                                <div>
                                    <span className="block text-blue-600">FX Rate</span>
                                    <span className="font-mono text-blue-900">{(details.fx_rate as number | string) || 'N/A'}</span>
                                </div>
                                <div>
                                    <span className="block text-blue-600">Value in INR</span>
                                    <span className="font-mono text-blue-900">
                                        {formatCurrency(
                                            Number(transaction.price_per_unit) * Number(transaction.quantity) * (Number(details.fx_rate) || 1),
                                            'INR'
                                        )}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* RSU Specific Details */}
                    {transaction.transaction_type === 'RSU_VEST' && (
                        <div className="bg-purple-50 p-3 rounded-md mb-4 border border-purple-100">
                            <h3 className="text-sm font-bold text-purple-800 mb-2">RSU Vest Details</h3>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                                <div>
                                    <span className="block text-purple-600">FMV at Vest</span>
                                    <span className="font-mono text-purple-900">{details.fmv ? formatCurrency(details.fmv as number, transaction.asset.currency) : 'N/A'}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Corporate Action Specific Details */}
                    {transaction.transaction_type === 'Corporate Action' && (
                        <div className="bg-orange-50 p-3 rounded-md mb-4 border border-orange-100">
                            <h3 className="text-sm font-bold text-orange-800 mb-2">Action Details</h3>
                            {/* Render logic for splits/bonus/spinoffs if needed */}
                        </div>
                    )}

                    {/* Raw Details View for transparency */}
                    {hasDetails && (
                        <div>
                            <span className="block text-gray-500 text-xs mb-1">Raw Metadata</span>
                            <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto text-gray-700 font-mono">
                                {JSON.stringify(details, null, 2)}
                            </pre>
                        </div>
                    )}
                </div>

                <div className="mt-6 flex justify-end">
                    <button onClick={onClose} className="btn btn-primary btn-sm">Close</button>
                </div>
            </div>
        </div>
    );
};

export default TransactionDetailsModal;

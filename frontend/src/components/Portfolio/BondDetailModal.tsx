import React from 'react';
import { Holding } from '../../types/holding';
import { Transaction } from '../../types/portfolio';
import { useAssetAnalytics, useAssetTransactions } from '../../hooks/usePortfolios';
import { usePrivacySensitiveCurrency, formatCurrency, formatDate, formatPercentage } from '../../utils/formatting';
import { XMarkIcon, PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline';

interface BondDetailModalProps {
    holding: Holding;
    portfolioId: string;
    onClose: () => void;
    onEditTransaction: (transaction: Transaction) => void;
    onDeleteTransaction: (transaction: Transaction) => void; // This was correct, but the parent component was passing the wrong function
}

const BondDetailModal: React.FC<BondDetailModalProps> = ({
    holding,
    portfolioId,
    onClose,
    onEditTransaction,
    onDeleteTransaction,
}) => {
    const formatSensitiveCurrency = usePrivacySensitiveCurrency();
    const { data: transactions, isLoading: isLoadingTransactions } = useAssetTransactions(portfolioId, holding.asset_id);
    const { data: analytics, isLoading: isLoadingAnalytics } = useAssetAnalytics(portfolioId, holding.asset_id);

    const sortedTransactions = transactions
        ? [...transactions].sort((a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime())
        : [];

    return (
        <div className="modal-overlay pt-safe pb-safe p-4" onClick={onClose}>
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby="bond-detail-modal-title"
                className="modal-content w-full max-w-3xl max-h-[90vh] flex flex-col border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="p-6 pb-2 flex-shrink-0">
                    <div id="bond-detail-modal-title" className="flex justify-between items-start mb-4 gap-4">
                        <div className="min-w-0">
                            <h2 className="text-xl sm:text-2xl font-bold dark:text-gray-100 break-words">{holding.asset_name}</h2>
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{holding.isin}</p>
                        </div>
                        <button aria-label="Close" onClick={onClose} className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:hover:text-gray-200 dark:hover:bg-gray-700 rounded-full w-8 h-8 flex-shrink-0 flex items-center justify-center transition-colors -mt-1 -mr-1">
                            <XMarkIcon className="h-6 w-6" />
                        </button>
                    </div>

                    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-2 bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <div className="min-w-0">
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">Coupon</p>
                            <p className="font-semibold dark:text-gray-100 truncate">{`${Number(holding.interest_rate || 0).toFixed(2)}%`}</p>
                        </div>
                        <div className="min-w-0">
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">Maturity</p>
                            <p className="font-semibold dark:text-gray-100 truncate">{holding.maturity_date ? formatDate(holding.maturity_date) : 'N/A'}</p>
                        </div>
                        <div className="min-w-0">
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">Current Value</p>
                            <p className="font-semibold dark:text-gray-100 truncate">{formatSensitiveCurrency(holding.current_value)}</p>
                        </div>
                        <div className="min-w-0">
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">Unrealized P&L</p>
                            <p className={`font-semibold truncate ${holding.unrealized_pnl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                                {formatSensitiveCurrency(holding.unrealized_pnl)}
                            </p>
                        </div>
                        <div className="min-w-0">
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">Annualized Return</p>
                            <p className="font-semibold dark:text-gray-100 truncate">
                                {isLoadingAnalytics ? '...' : formatPercentage(analytics?.xirr_current ?? 0)}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto px-6 py-2 min-h-0">
                    <h3 className="text-lg font-semibold mb-2 dark:text-gray-100">Transaction History</h3>
                    {isLoadingTransactions ? <p className="dark:text-gray-300">Loading transactions...</p> : (
                        <div className="overflow-x-auto w-full">
                            <table className="table-auto w-full min-w-[600px]">
                                <thead className="sticky top-0 bg-white dark:bg-gray-800 shadow-sm z-10">
                                    <tr className="text-left text-gray-600 dark:text-gray-400 text-sm">
                                        <th className="p-2 whitespace-nowrap">Date</th>
                                        <th className="p-2 whitespace-nowrap">Type</th>
                                        <th className="p-2 text-right whitespace-nowrap">Quantity</th>
                                        <th className="p-2 text-right whitespace-nowrap">Price</th>
                                        <th className="p-2 text-right whitespace-nowrap">Total Value</th>
                                        <th className="p-2 text-center whitespace-nowrap">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sortedTransactions.map(tx => (
                                        <tr key={tx.id} className="border-t dark:border-gray-700">
                                            <td className="p-2 dark:text-gray-200">{formatDate(tx.transaction_date)}</td>
                                            <td className={`p-2 font-semibold ${tx.transaction_type === 'BUY' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>{tx.transaction_type}</td>
                                            <td className="p-2 text-right font-mono dark:text-gray-200">{Number(tx.quantity).toLocaleString()}</td>
                                            <td className="p-2 text-right font-mono dark:text-gray-200">{formatCurrency(tx.price_per_unit)}</td>
                                            <td className="p-2 text-right font-mono dark:text-gray-200">{formatCurrency(Number(tx.quantity) * Number(tx.price_per_unit))}</td>
                                            <td className="p-2 text-center">
                                                <div className="flex items-center justify-center space-x-3">
                                                    <button aria-label={`Edit transaction for ${holding.asset_name}`} onClick={() => onEditTransaction(tx)} className="text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400" title="Edit Transaction"><PencilSquareIcon className="h-5 w-5" /></button>
                                                    <button aria-label={`Delete transaction for ${holding.asset_name}`} onClick={() => onDeleteTransaction(tx)} className="text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400" title="Delete Transaction"><TrashIcon className="h-5 w-5" /></button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                <div className="p-6 pt-4 flex-shrink-0 flex justify-end space-x-2 border-t border-gray-100 dark:border-gray-700">
                    <button onClick={onClose} className="btn btn-secondary">Close</button>
                </div>
            </div>
        </div>
    );
};

export default BondDetailModal;
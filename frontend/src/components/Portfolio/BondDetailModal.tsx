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
    onDeleteTransaction: (transaction: Transaction) => void;
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
        <div className="modal-overlay" onClick={onClose}>
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby="bond-detail-modal-title"
                className="modal-content w-full max-w-3xl p-6 border border-gray-200 rounded-lg shadow-xl"
                onClick={(e) => e.stopPropagation()}
            >
                <div id="bond-detail-modal-title" className="flex justify-between items-center mb-4">
                    <div>
                        <h2 className="text-2xl font-bold">{holding.asset_name}</h2>
                        <p className="text-sm text-gray-500">{holding.isin}</p>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-full w-8 h-8 flex items-center justify-center transition-colors -mr-2 -mt-2">
                        <XMarkIcon className="h-6 w-6" />
                    </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-6 bg-gray-50 p-4 rounded-lg">
                    <div>
                        <p className="text-sm text-gray-500">Coupon</p>
                        <p className="font-semibold">{formatPercentage(holding.interest_rate || 0)}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Maturity</p>
                        <p className="font-semibold">{holding.maturity_date}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Current Value</p>
                        <p className="font-semibold">{formatSensitiveCurrency(holding.current_value)}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Annualized (XIRR)</p>
                        <p className="font-semibold">
                            {isLoadingAnalytics ? '...' : `${((analytics?.unrealized_xirr ?? 0) * 100).toFixed(2)}%`}
                        </p>
                    </div>
                </div>

                <div className="overflow-y-auto max-h-96">
                    <h3 className="text-lg font-semibold mb-2">Transaction History</h3>
                    {isLoadingTransactions ? <p>Loading transactions...</p> : (
                        <table className="table-auto w-full">
                            <thead className="sticky top-0 bg-white shadow-sm">
                                <tr className="text-left text-gray-600 text-sm">
                                    <th className="p-2">Date</th>
                                    <th className="p-2">Type</th>
                                    <th className="p-2 text-right">Quantity</th>
                                    <th className="p-2 text-right">Price</th>
                                    <th className="p-2 text-right">Total Value</th>
                                    <th className="p-2 text-center">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sortedTransactions.map(tx => (
                                    <tr key={tx.id} className="border-t">
                                        <td className="p-2">{formatDate(tx.transaction_date)}</td>
                                        <td className={`p-2 font-semibold ${tx.transaction_type === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>{tx.transaction_type}</td>
                                        <td className="p-2 text-right font-mono">{Number(tx.quantity).toLocaleString()}</td>
                                        <td className="p-2 text-right font-mono">{formatCurrency(tx.price_per_unit)}</td>
                                        <td className="p-2 text-right font-mono">{formatCurrency(Number(tx.quantity) * Number(tx.price_per_unit))}</td>
                                        <td className="p-2 text-center">
                                            <div className="flex items-center justify-center space-x-3">
                                                <button onClick={() => onEditTransaction(tx)} className="text-gray-500 hover:text-blue-600" title="Edit Transaction"><PencilSquareIcon className="h-5 w-5" /></button>
                                                <button onClick={() => onDeleteTransaction(tx)} className="text-gray-500 hover:text-red-600" title="Delete Transaction"><TrashIcon className="h-5 w-5" /></button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
                <div className="flex justify-end mt-6">
                    <button onClick={onClose} className="btn btn-secondary">Close</button>
                </div>
            </div>
        </div>
    );
};

export default BondDetailModal;


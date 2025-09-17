import React, { useMemo } from 'react';
import { Holding } from '../../types/holding';
import { Transaction } from '../../types/portfolio';
import { useAssetAnalytics, useAssetTransactions } from '../../hooks/usePortfolios';
import { usePrivacySensitiveCurrency, formatCurrency, formatDate } from '../../utils/formatting';
import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline';

interface HoldingDetailModalProps {
    holding: Holding;
    portfolioId: string;
    onClose: () => void;
    onEditTransaction: (transaction: Transaction) => void;
    onDeleteTransaction: (transaction: Transaction) => void;
}

const calculateCagr = (buyPrice: number, currentPrice: number, buyDate: string): number | null => {
    if (buyPrice <= 0) return null;

    const startDate = new Date(buyDate);
    const endDate = new Date();

    const years = (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24 * 365.25);

    if (years <= 0) return null;

    const cagr = Math.pow(currentPrice / buyPrice, 1 / years) - 1;

    return cagr * 100;
};

interface TransactionRowProps {
    transaction: Transaction;
    currentPrice: number;
    onEdit: (transaction: Transaction) => void;
    onDelete: (transaction: Transaction) => void;
}

const TransactionRow: React.FC<TransactionRowProps> = ({ transaction, currentPrice, onEdit, onDelete }) => {
    const cagr = transaction.transaction_type === 'BUY'
        ? calculateCagr(Number(transaction.price_per_unit), currentPrice, transaction.transaction_date)
        : null;

    return (
        <tr className="border-t">
            <td className="p-2">{formatDate(transaction.transaction_date)}</td>
            <td className={`p-2 font-semibold ${transaction.transaction_type === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>
                {transaction.transaction_type}
            </td>
            <td className="p-2 text-right font-mono">{Number(transaction.quantity).toLocaleString()}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(transaction.price_per_unit)}</td>
            <td className="p-2 text-right font-mono">{formatCurrency(Number(transaction.quantity) * Number(transaction.price_per_unit))}</td>
            <td className="p-2 text-right font-mono">
                {cagr !== null ? `${cagr.toFixed(2)}%` : 'N/A'}
            </td>
            <td className="p-2 text-right">
                <div className="flex items-center justify-end space-x-3">
                    <button onClick={() => onEdit(transaction)} className="text-gray-500 hover:text-blue-600" title="Edit Transaction">
                        <PencilSquareIcon className="h-5 w-5" />
                    </button>
                    <button onClick={() => onDelete(transaction)} className="text-gray-500 hover:text-red-600" title="Delete Transaction">
                        <TrashIcon className="h-5 w-5" />
                    </button>
                </div>
            </td>
        </tr>
    );
};

const HoldingDetailModal: React.FC<HoldingDetailModalProps> = ({ holding, portfolioId, onClose, onEditTransaction, onDeleteTransaction }) => {
    const { data: transactions, isLoading, error } = useAssetTransactions(portfolioId, holding.asset_id);
    const { data: analytics, isLoading: isLoadingAnalytics, isError: isErrorAnalytics } = useAssetAnalytics(portfolioId, holding.asset_id);
    const formatSensitiveCurrency = usePrivacySensitiveCurrency();

    const openTransactions = useMemo(() => {
        if (!transactions) return [];

        const sortedTxs = [...transactions].sort((a, b) => new Date(a.transaction_date).getTime() - new Date(b.transaction_date).getTime());

        const buys = JSON.parse(JSON.stringify(sortedTxs.filter(tx => tx.transaction_type === 'BUY')));
        const sells = JSON.parse(JSON.stringify(sortedTxs.filter(tx => tx.transaction_type === 'SELL')));

        for (const sell of sells) {
            let sellQuantityToMatch = Number(sell.quantity);
            for (const buy of buys) {
                if (sellQuantityToMatch <= 0) break;
                const buyQuantity = Number(buy.quantity);
                if (buyQuantity > 0) {
                    const matchQuantity = Math.min(sellQuantityToMatch, buyQuantity);
                    buy.quantity = String(buyQuantity - matchQuantity);
                    sellQuantityToMatch -= matchQuantity;
                }
            }
        }
        return buys.filter((buy: Transaction) => Number(buy.quantity) > 0.000001);
    }, [transactions]);

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div role="dialog" aria-modal="true" aria-labelledby="holding-detail-modal-title" className="modal-content w-full max-w-3xl p-6 border border-gray-200 rounded-lg shadow-xl" onClick={(e) => e.stopPropagation()}>
                <div id="holding-detail-modal-title" className="flex justify-between items-center mb-4">
                    <div>
                        <h2 className="text-2xl font-bold">
                            {holding.asset_name} {holding.asset_type !== 'Mutual Fund' && `(${holding.ticker_symbol})`}
                        </h2>
                        <p className="text-sm text-gray-500">Transaction History</p>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-full w-8 h-8 flex items-center justify-center transition-colors -mr-2 -mt-2">
                        <span className="text-2xl leading-none">&times;</span>
                    </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6 bg-gray-50 p-4 rounded-lg">
                    <div data-testid="summary-quantity">
                        <p className="text-sm text-gray-500">Quantity</p>
                        <p className="font-semibold">{Number(holding.quantity).toLocaleString()}</p>
                    </div>
                    <div data-testid="summary-avg-buy-price">
                        <p className="text-sm text-gray-500">Avg. Buy Price</p>
                        <p className="font-semibold">{formatSensitiveCurrency(holding.average_buy_price)}</p>
                    </div>
                    <div data-testid="summary-current-value">
                        <p className="text-sm text-gray-500">Current Value</p>
                        <p className="font-semibold">{formatSensitiveCurrency(holding.current_value)}</p>
                    </div>
                    <div data-testid="summary-unrealized-pnl">
                        <p className="text-sm text-gray-500">Unrealized P&L</p>
                        <p className={`font-semibold ${holding.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatSensitiveCurrency(holding.unrealized_pnl)}
                        </p>
                    </div>
                    <div data-testid="summary-realized-xirr">
                        <p className="text-sm text-gray-500">Realized XIRR</p>
                        <p className="font-semibold">
                            {isLoadingAnalytics ? '...' : isErrorAnalytics ? 'N/A' : `${((analytics?.realized_xirr ?? 0) * 100).toFixed(2)}%`}
                        </p>
                    </div>
                    <div data-testid="summary-unrealized-xirr">
                        <p className="text-sm text-gray-500">Unrealized XIRR</p>
                        <p className="font-semibold">
                            {isLoadingAnalytics ? '...' : isErrorAnalytics ? 'N/A' : `${((analytics?.unrealized_xirr ?? 0) * 100).toFixed(2)}%`}
                        </p>
                    </div>
                </div>

                <div className="overflow-y-auto max-h-96">
                    {isLoading && <p className="text-center p-4">Loading transactions...</p>}
                    {error && <p className="text-red-500 text-center p-4">Error loading transactions: {error.message}</p>}
                    {transactions && (
                        <table className="table-auto w-full">
                            <thead className="sticky top-0 bg-white shadow-sm">
                                <tr className="text-left text-gray-600 text-sm">
                                    <th className="p-2">Date</th>
                                    <th className="p-2">Type</th>
                                    <th className="p-2 text-right">Quantity</th>
                                    <th className="p-2 text-right">Price/Unit</th>
                                    <th className="p-2 text-right">Total Value</th>
                                    <th className="p-2 text-right">CAGR %</th>
                                    <th className="p-2 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {openTransactions.map(tx => <TransactionRow key={tx.id} transaction={tx} currentPrice={holding.current_price} onEdit={onEditTransaction} onDelete={onDeleteTransaction} />)}
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

export default HoldingDetailModal;
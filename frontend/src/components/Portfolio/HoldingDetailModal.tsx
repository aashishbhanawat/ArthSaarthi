import React, { useMemo } from 'react';
import { Holding } from '../../types/holding';
import { Transaction } from '../../types/portfolio';
import { useAssetAnalytics, useAssetTransactions } from '../../hooks/usePortfolios';
import { usePrivacySensitiveCurrency, formatCurrency, formatDate } from '../../utils/formatting';
import { PencilSquareIcon, TrashIcon, XMarkIcon } from '@heroicons/react/24/outline';

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
    demergerInfo: {
        ratio: number;
        earliestDemergerDate: string | null;
    };
    onEdit: (tx: Transaction) => void;
    onDelete: (tx: Transaction) => void;
}

const TransactionRow: React.FC<TransactionRowProps> = ({ transaction, currentPrice, demergerInfo, onEdit, onDelete }) => {
    // Scale price by cost reduction ratio for demerged parent assets (only for BUYs before demerger)
    const originalPrice = Number(transaction.price_per_unit);
    const txDate = new Date(transaction.transaction_date);
    const demergerDate = demergerInfo.earliestDemergerDate ? new Date(demergerInfo.earliestDemergerDate) : null;

    // Only apply adjustment if: ratio < 1, transaction is before demerger date
    const shouldApplyAdjustment = demergerInfo.ratio < 1 && demergerDate && txDate < demergerDate;
    const adjustedPrice = shouldApplyAdjustment ? originalPrice * demergerInfo.ratio : originalPrice;
    const hasDemergerAdjustment = shouldApplyAdjustment;

    const cagr = transaction.transaction_type === 'BUY'
        ? calculateCagr(adjustedPrice, currentPrice, transaction.transaction_date)
        : null;

    return (
        <tr className="border-t dark:border-gray-700">
            <td className="p-2 dark:text-gray-200">{formatDate(transaction.transaction_date)}</td>
            <td className={`p-2 font-semibold ${transaction.transaction_type === 'BUY' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {transaction.transaction_type}
            </td>
            <td className="p-2 text-right font-mono dark:text-gray-200">{Number(transaction.quantity).toLocaleString('en-IN', { maximumFractionDigits: 4 })}</td>
            <td className="p-2 text-right font-mono dark:text-gray-200" title={hasDemergerAdjustment ? `Adjusted for demerger. Original: ${formatCurrency(originalPrice, 'INR')}` : undefined}>
                {hasDemergerAdjustment ? (
                    <span>
                        {formatCurrency(adjustedPrice, 'INR')}
                        <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">(orig: {formatCurrency(originalPrice, 'INR')})</span>
                    </span>
                ) : (
                    formatCurrency(originalPrice, 'INR')
                )}
            </td>
            <td className="p-2 text-right font-mono dark:text-gray-200">{formatCurrency(Number(transaction.quantity) * adjustedPrice, 'INR')}</td>
            <td className="p-2 text-right font-mono dark:text-gray-200">
                {cagr !== null ? `${cagr.toFixed(2)}%` : 'N/A'}
            </td>
            <td className="p-2 text-right">
                <div className="flex items-center justify-end space-x-3">
                    <button onClick={() => onEdit(transaction)} className="text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400" title="Edit Transaction">
                        <PencilSquareIcon className="h-5 w-5" />
                    </button>
                    <button onClick={() => onDelete(transaction)} className="text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400" title="Delete Transaction">
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

    const { demergerInfo, openTransactions } = useMemo(() => {
        if (!transactions) return { demergerInfo: { ratio: 1, earliestDemergerDate: null }, openTransactions: [] };

        const sortedTxs = [...transactions].sort((a, b) => new Date(a.transaction_date).getTime() - new Date(b.transaction_date).getTime());

        // First pass: find earliest demerger date and total cost reduction
        let totalCostReduction = 0;
        let earliestDemergerDate: string | null = null;
        const acquisitionTypes = ['BUY', 'RSU_VEST', 'ESPP_PURCHASE'];

        for (const tx of sortedTxs) {
            if (tx.transaction_type === 'DEMERGER' && tx.details?.total_cost_allocated) {
                totalCostReduction += Number(tx.details.total_cost_allocated);
                if (!earliestDemergerDate || tx.transaction_date < earliestDemergerDate) {
                    earliestDemergerDate = tx.transaction_date;
                }
            }
        }

        // Second pass: calculate cost of BUYs BEFORE demerger date only
        let preDemergerCost = 0;
        const demergerDateObj = earliestDemergerDate ? new Date(earliestDemergerDate) : null;
        for (const tx of sortedTxs) {
            if (acquisitionTypes.includes(tx.transaction_type)) {
                // Only count if no demerger OR buy is before demerger
                if (!demergerDateObj || new Date(tx.transaction_date) < demergerDateObj) {
                    preDemergerCost += Number(tx.quantity) * Number(tx.price_per_unit);
                }
            }
        }

        // Ratio = remaining cost / original pre-demerger cost
        const ratio = preDemergerCost > 0 && totalCostReduction > 0
            ? (preDemergerCost - totalCostReduction) / preDemergerCost
            : 1;

        // Include RSU_VEST and ESPP_PURCHASE as acquisition types alongside BUY
        const buys = JSON.parse(JSON.stringify(sortedTxs.filter(tx => acquisitionTypes.includes(tx.transaction_type))));
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
        return {
            demergerInfo: { ratio, earliestDemergerDate },
            openTransactions: buys.filter((buy: Transaction) => Number(buy.quantity) > 0.000001)
        };
    }, [transactions]);

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div role="dialog" aria-modal="true" aria-labelledby="holding-detail-modal-title" className="modal-content w-full max-w-6xl p-6 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl" onClick={(e) => e.stopPropagation()}>
                <div id="holding-detail-modal-title" className="flex justify-between items-center mb-4">
                    <div>
                        <h2 className="text-2xl font-bold dark:text-gray-100">
                            {holding.asset_name} {holding.asset_type !== 'Mutual Fund' && `(${holding.ticker_symbol})`}
                        </h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Transaction History</p>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:hover:text-gray-200 dark:hover:bg-gray-700 rounded-full w-8 h-8 flex items-center justify-center transition-colors -mr-2 -mt-2">
                        <XMarkIcon className="h-6 w-6" />
                    </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-4 bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div data-testid="summary-quantity">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Quantity</p>
                        <p className="font-semibold dark:text-gray-100">{Number(holding.quantity).toLocaleString()}</p>
                    </div>
                    <div data-testid="summary-avg-buy-price">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Avg. Buy Price</p>
                        <p className="font-semibold dark:text-gray-100">{formatSensitiveCurrency(holding.average_buy_price, 'INR')}</p>
                    </div>
                    <div data-testid="summary-current-value">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Current Value</p>
                        <p className="font-semibold dark:text-gray-100">{formatSensitiveCurrency(holding.current_value)}</p>
                    </div>
                    <div data-testid="summary-unrealized-pnl">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Unrealized P&L</p>
                        <p className={`font-semibold ${holding.unrealized_pnl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                            {formatSensitiveCurrency(holding.unrealized_pnl)}
                        </p>
                    </div>
                    <div data-testid="summary-realized-pnl">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Capital Gains</p>
                        <p className={`font-semibold ${(analytics?.realized_pnl ?? 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                            {isLoadingAnalytics ? '...' : isErrorAnalytics ? 'N/A' : formatSensitiveCurrency(analytics?.realized_pnl ?? 0)}
                        </p>
                    </div>
                    <div data-testid="summary-dividend-income">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Dividend Income</p>
                        <p className="font-semibold text-green-600 dark:text-green-400">
                            {isLoadingAnalytics ? '...' : isErrorAnalytics ? 'N/A' : formatSensitiveCurrency(analytics?.dividend_income ?? 0)}
                        </p>
                    </div>
                    <div data-testid="summary-xirr-current">
                        <p className="text-sm text-gray-500 dark:text-gray-400">XIRR (Current)</p>
                        <p className="font-semibold dark:text-gray-100">
                            {isLoadingAnalytics ? '...' : isErrorAnalytics ? 'N/A' : `${((analytics?.xirr_current ?? 0) * 100).toFixed(2)}%`}
                        </p>
                    </div>
                    <div data-testid="summary-xirr-historical">
                        <p className="text-sm text-gray-500 dark:text-gray-400">XIRR (Historical)</p>
                        <p className="font-semibold dark:text-gray-100">
                            {isLoadingAnalytics ? '...' : isErrorAnalytics ? 'N/A' : `${((analytics?.xirr_historical ?? 0) * 100).toFixed(2)}%`}
                        </p>
                    </div>
                </div>

                <div className="overflow-y-auto max-h-96">
                    {isLoading && <p className="text-center p-4 dark:text-gray-300">Loading transactions...</p>}
                    {error && <p className="text-red-500 text-center p-4">Error loading transactions: {error.message}</p>}
                    {transactions && (
                        <table className="table-auto w-full">
                            <thead className="sticky top-0 bg-white dark:bg-gray-800 shadow-sm">
                                <tr className="text-left text-gray-600 dark:text-gray-400 text-sm">
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
                                {openTransactions.map((tx: Transaction) => <TransactionRow key={tx.id} transaction={tx} currentPrice={holding.current_price} demergerInfo={demergerInfo} onEdit={onEditTransaction} onDelete={onDeleteTransaction} />)}
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
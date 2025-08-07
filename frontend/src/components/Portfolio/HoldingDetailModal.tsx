import React, { useMemo } from 'react';
import { Holding } from '../../types/holding';
import { Transaction } from '../../types/portfolio';
import { useAssetTransactions } from '../../hooks/usePortfolios';
import { formatCurrency, formatDate } from '../../utils/formatting';

interface HoldingDetailModalProps {
    holding: Holding;
    portfolioId: string;
    onClose: () => void;
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

const TransactionRow: React.FC<{ transaction: Transaction; currentPrice: number }> = ({ transaction, currentPrice }) => {
    const cagr = calculateCagr(Number(transaction.price_per_unit), currentPrice, transaction.transaction_date);

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
        </tr>
    );
};

const getConstituentBuyTransactions = (transactions: Transaction[] | undefined): Transaction[] => {
    if (!transactions || transactions.length === 0) return [];

    const sortedTxs = [...transactions].sort(
        (a, b) => new Date(a.transaction_date).getTime() - new Date(b.transaction_date).getTime()
    );

    const buys = sortedTxs.filter(tx => tx.transaction_type === 'BUY');
    const sells = sortedTxs.filter(tx => tx.transaction_type === 'SELL');

    let totalSold = sells.reduce((acc, tx) => acc + Number(tx.quantity), 0);

    const openBuys: Transaction[] = [];
    for (const buy of buys) {
        if (totalSold <= 0) {
            openBuys.push(buy);
            continue;
        }

        const buyQuantity = Number(buy.quantity);
        if (totalSold >= buyQuantity) {
            totalSold -= buyQuantity;
        } else {
            const remainingQuantity = buyQuantity - totalSold;
            totalSold = 0;
            openBuys.push({ ...buy, quantity: remainingQuantity });
        }
    }
    return openBuys;
};

const HoldingDetailModal: React.FC<HoldingDetailModalProps> = ({ holding, portfolioId, onClose }) => {
    const { data: transactions, isLoading, error } = useAssetTransactions(portfolioId, holding.asset_id);
    const constituentBuyTransactions = useMemo(() => getConstituentBuyTransactions(transactions), [transactions]);

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content w-full max-w-3xl p-6 border border-gray-200 rounded-lg shadow-xl" onClick={(e) => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h2 className="text-2xl font-bold">{holding.asset_name} ({holding.ticker_symbol})</h2>
                        <p className="text-sm text-gray-500">Transaction History</p>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-full w-8 h-8 flex items-center justify-center transition-colors -mr-2 -mt-2">
                        <span className="text-2xl leading-none">&times;</span>
                    </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 bg-gray-50 p-4 rounded-lg">
                    <div>
                        <p className="text-sm text-gray-500">Quantity</p>
                        <p className="font-semibold">{Number(holding.quantity).toLocaleString()}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Avg. Buy Price</p>
                        <p className="font-semibold">{formatCurrency(holding.average_buy_price)}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Current Value</p>
                        <p className="font-semibold">{formatCurrency(holding.current_value)}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Unrealized P&L</p>
                        <p className={`font-semibold ${holding.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(holding.unrealized_pnl)}
                        </p>
                    </div>
                </div>

                <div className="overflow-y-auto max-h-96">
                    {isLoading && <p className="text-center p-4">Loading transactions...</p>}
                    {error && <p className="text-red-500 text-center p-4">Error loading transactions: {error.message}</p>}
                    {constituentBuyTransactions && (
                        <table className="table-auto w-full">
                            <thead className="sticky top-0 bg-white shadow-sm">
                                <tr className="text-left text-gray-600 text-sm">
                                    <th className="p-2">Date</th>
                                    <th className="p-2">Type</th>
                                    <th className="p-2 text-right">Quantity</th>
                                    <th className="p-2 text-right">Price/Unit</th>
                                    <th className="p-2 text-right">Total Value</th>
                                    <th className="p-2 text-right">CAGR %</th>
                                </tr>
                            </thead>
                            <tbody>
                                {constituentBuyTransactions.map(tx => <TransactionRow key={tx.id} transaction={tx} currentPrice={holding.current_price} />)}
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
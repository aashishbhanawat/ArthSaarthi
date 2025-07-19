import React from 'react';
import { Transaction } from '../../types/portfolio';

interface TransactionListProps {
    transactions: Transaction[];
}

const TransactionList: React.FC<TransactionListProps> = ({ transactions }) => {
    if (transactions.length === 0) {
        return <p className="text-center text-gray-500 mt-8">No transactions found for this portfolio.</p>;
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString();
    };

    return (
        <div className="overflow-x-auto card">
            <table className="min-w-full bg-white">
                <thead className="bg-gray-200">
                    <tr>
                        <th className="text-left py-3 px-4 uppercase font-semibold text-sm">Date</th>
                        <th className="text-left py-3 px-4 uppercase font-semibold text-sm">Type</th>
                        <th className="text-left py-3 px-4 uppercase font-semibold text-sm">Asset</th>
                        <th className="text-right py-3 px-4 uppercase font-semibold text-sm">Quantity</th>
                        <th className="text-right py-3 px-4 uppercase font-semibold text-sm">Price/Unit</th>
                        <th className="text-right py-3 px-4 uppercase font-semibold text-sm">Total Value</th>
                    </tr>
                </thead>
                <tbody className="text-gray-700">
                    {transactions.map((tx) => (
                        <tr key={tx.id} className="border-b odd:bg-gray-50">
                            <td className="text-left py-3 px-4">{formatDate(tx.transaction_date)}</td>
                            <td className={`text-left py-3 px-4 font-bold ${tx.transaction_type === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>
                                {tx.transaction_type}
                            </td>
                            <td className="text-left py-3 px-4">
                                <div className="font-semibold">{tx.asset.name}</div>
                                <div className="text-xs text-gray-500">{tx.asset.ticker_symbol}</div>
                            </td>
                            <td className="text-right py-3 px-4">{parseFloat(tx.quantity).toFixed(4)}</td>
                            <td className="text-right py-3 px-4">${parseFloat(tx.price_per_unit).toFixed(2)}</td>
                            <td className="text-right py-3 px-4 font-semibold">${(parseFloat(tx.quantity) * parseFloat(tx.price_per_unit)).toFixed(2)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default TransactionList;
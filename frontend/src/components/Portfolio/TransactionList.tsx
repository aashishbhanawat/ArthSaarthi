import React from 'react';
import { Transaction } from '../../types/portfolio';
import { formatCurrency } from '../../utils/formatting';

interface TransactionListProps {
  transactions: Transaction[];
}

const TransactionList: React.FC<TransactionListProps> = ({ transactions }) => {
  if (!transactions || transactions.length === 0) {
    return (
      <div className="card text-center p-8">
        <p className="text-gray-500">No transactions found for this portfolio.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-xl font-bold mb-4">Transactions</h2>
      <div className="overflow-x-auto">
        <table className="table-auto w-full">
          <thead>
            <tr className="text-left text-gray-600">
              <th className="p-2">Date</th>
              <th className="p-2">Asset</th>
              <th className="p-2">Type</th>
              <th className="p-2 text-right">Quantity</th>
              <th className="p-2 text-right">Price</th>
              <th className="p-2 text-right">Total Value</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx.id} className="border-t">
                <td className="p-2">{new Date(tx.transaction_date).toLocaleDateString()}</td>
                <td className="p-2">
                  <div className="font-bold">{tx.asset.ticker_symbol}</div>
                  <div className="text-sm text-gray-500">{tx.asset.name}</div>
                </td>
                <td className={`p-2 font-bold ${tx.transaction_type === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>
                  {tx.transaction_type}
                </td>
                <td className="p-2 text-right font-mono">{Number(tx.quantity).toLocaleString()}</td>
                <td className="p-2 text-right font-mono">{formatCurrency(Number(tx.price_per_unit))}</td>
                <td className="p-2 text-right font-mono">{formatCurrency(Number(tx.quantity) * Number(tx.price_per_unit))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TransactionList;

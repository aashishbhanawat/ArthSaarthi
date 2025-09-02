import React from 'react';
import { Transaction } from '../../types/portfolio';
import { formatCurrency, formatDate } from '../../utils/formatting';
import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline';

interface TransactionListProps {
  transactions: Transaction[];
  onEdit: (transaction: Transaction) => void;
  onDelete: (transaction: Transaction) => void;
}

const TransactionList: React.FC<TransactionListProps> = ({ transactions, onEdit, onDelete }) => {
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
              <th className="p-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx.id} className="border-t">
                <td className="p-2">{formatDate(tx.transaction_date)}</td>
                <td className="p-2">
                  {/* For Mutual Funds, the name is sufficient and the ticker (scheme code) is not user-friendly. */}
                  {tx.asset.asset_type !== 'Mutual Fund' && <div className="font-bold">{tx.asset.ticker_symbol}</div>}
                  <div className={`text-sm ${tx.asset.asset_type !== 'Mutual Fund' ? 'text-gray-500' : 'font-semibold text-gray-900'}`}>
                    {tx.asset.name}
                  </div>
                </td>
                <td className="p-2">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    tx.transaction_type === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {tx.transaction_type}
                  </span>
                </td>
                <td className="p-2 text-right font-mono">{Number(tx.quantity).toLocaleString()}</td>
                <td className="p-2 text-right font-mono">{formatCurrency(Number(tx.price_per_unit))}</td>
                <td className="p-2 text-right font-mono">{formatCurrency(Number(tx.quantity) * Number(tx.price_per_unit))}</td>
                <td className="p-2 text-right">
                  <div className="flex justify-end space-x-2">
                    <button onClick={() => onEdit(tx)} className="p-1 text-gray-500 hover:text-blue-600" aria-label={`Edit transaction for ${tx.asset.ticker_symbol}`}>
                      <PencilSquareIcon className="h-5 w-5" />
                    </button>
                    <button onClick={() => onDelete(tx)} className="p-1 text-gray-500 hover:text-red-600" aria-label={`Delete transaction for ${tx.asset.ticker_symbol}`}>
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TransactionList;

import React from 'react';
import { Transaction } from '../../types/portfolio';
import { usePrivacySensitiveCurrency, formatDate } from '../../utils/formatting';
import { PencilSquareIcon, TrashIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

interface TransactionListProps {
  transactions: Transaction[];
  // Note: The parent component should handle fetching portfolio details if needed
  onEdit: (transaction: Transaction) => void;
  onDelete: (transaction: Transaction) => void;
}

const TransactionList: React.FC<TransactionListProps> = ({ transactions, onEdit, onDelete }) => {
  const formatCurrency = usePrivacySensitiveCurrency();

  if (!transactions || transactions.length === 0) {
    return (
      <div className="card text-center p-12 bg-gray-50/50 dark:bg-gray-800/50 border border-dashed border-gray-200 dark:border-gray-700">
        <div className="flex flex-col items-center justify-center space-y-3">
          <DocumentTextIcon className="h-12 w-12 text-gray-400 dark:text-gray-500" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">No transactions</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm">
            There are no transactions recorded for this portfolio yet. Use the "Add Transaction" button above to get started.
          </p>
        </div>
      </div>
    );
  }

  const getTransactionTypeStyle = (type: string) => {
    switch (type) {
      case 'BUY':
      case 'CONTRIBUTION':
        return 'bg-green-100 text-green-800';
      case 'SELL':
        return 'bg-red-100 text-red-800';
      case 'RSU_VEST':
      case 'ESPP_PURCHASE':
        return 'bg-purple-100 text-purple-800';
      case 'DIVIDEND':
      case 'COUPON':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="card">
      <h2 className="text-xl font-bold mb-4">Transactions</h2>
      <div className="overflow-x-auto">
        <table className="table-auto w-full">
          <thead>
            <tr className="text-left text-gray-600 text-sm">
              <th className="p-3">Date</th>
              <th className="p-3">Asset</th>
              <th className="p-3">Type</th>
              <th className="p-3 text-right">Quantity</th>
              <th className="p-3 text-right">Price/Unit</th>
              <th className="p-3 text-right">Total Value</th>
              <th className="p-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx.id} className="border-b hover:bg-gray-50 text-sm">
                <td className="p-3">{formatDate(tx.transaction_date)}</td>
                <td className="p-3">
                  <div className="font-bold">{tx.asset.ticker_symbol}</div>
                  <div className="text-xs text-gray-500">{tx.asset.name}</div>
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getTransactionTypeStyle(tx.transaction_type)}`}>
                    {tx.transaction_type}
                  </span>
                </td>
                <td className="p-3 text-right font-mono">{Number(tx.quantity).toLocaleString('en-IN', { maximumFractionDigits: tx.asset.asset_type === 'FIXED_DEPOSIT' ? 0 : 4 })}</td>
                <td className="p-3 text-right font-mono">{formatCurrency(tx.price_per_unit, tx.asset.currency)}</td>
                <td className="p-3 text-right font-mono">{formatCurrency(
                  Number(tx.price_per_unit) * Number(tx.quantity) * (Number(tx.details?.fx_rate) || 1),
                  'INR'
                )}</td>
                <td className="p-3 text-center">
                  <div className="flex justify-center space-x-2">
                    <button onClick={() => onEdit(tx)} className="p-1 text-gray-500 hover:text-blue-600" aria-label={`Edit transaction for ${tx.asset.ticker_symbol}`}><PencilSquareIcon className="h-5 w-5" /></button>
                    <button onClick={() => onDelete(tx)} className="p-1 text-gray-500 hover:text-red-600" aria-label={`Delete transaction for ${tx.asset.ticker_symbol}`}><TrashIcon className="h-5 w-5" /></button>
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

import React from 'react';
import { Transaction } from '~/types/portfolio';
import { formatCurrency, formatDate } from '~/utils/formatting';
import { PencilSquareIcon, TrashIcon, InformationCircleIcon } from '@heroicons/react/24/outline';
import Tooltip from '~/components/common/Tooltip';

interface TransactionListProps {
  transactions: Transaction[];
  onEdit: (transaction: Transaction) => void;
  onDelete: (transaction: Transaction) => void;
}

const getTransactionTypeStyle = (type: string) => {
    switch (type) {
        case 'BUY':
        case 'ESPP_PURCHASE':
        case 'RSU_VEST':
            return 'bg-green-100 text-green-800';
        case 'SELL':
            return 'bg-red-100 text-red-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
};

const TransactionDetailTooltip: React.FC<{ details: Record<string, unknown> | null }> = ({ details }) => {
    if (!details) return null;

    return (
        <div className="space-y-1">
            {Object.entries(details).map(([key, value]) => (
                <div key={key}>
                    <span className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</span>{' '}
                    <span>{typeof value === 'number' ? formatCurrency(value, 'INR') : String(value)}</span>
                </div>
            ))}
        </div>
    );
};

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
                  {tx.asset.asset_type !== 'Mutual Fund' && <div className="font-bold">{tx.asset.ticker_symbol}</div>}
                  <div className={`text-sm ${tx.asset.asset_type !== 'Mutual Fund' ? 'text-gray-500' : 'font-semibold text-gray-900'}`}>
                    {tx.asset.name}
                  </div>
                </td>
                <td className="p-2">
                    <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getTransactionTypeStyle(tx.transaction_type)}`}>
                            {tx.transaction_type.replace('_', ' ')}
                        </span>
                        {tx.details && (
                            <Tooltip content={<TransactionDetailTooltip details={tx.details} />}>
                                <InformationCircleIcon className="h-5 w-5 text-gray-400" />
                            </Tooltip>
                        )}
                    </div>
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

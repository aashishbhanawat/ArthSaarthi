
import React from 'react';
import { Transaction } from '~/types/portfolio';
import { formatCurrency, formatDate } from '~/utils/formatting';
import { InformationCircleIcon } from '@heroicons/react/24/outline';
import Tooltip from '~/components/common/Tooltip';

interface TransactionHistoryTableProps {
  transactions: Transaction[];
  onEdit: (transaction: Transaction) => void;
  onDelete: (transaction: Transaction) => void;
}

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

const TransactionHistoryTable: React.FC<TransactionHistoryTableProps> = ({ transactions, onEdit, onDelete }) => {
  if (transactions.length === 0) {
    return <div className="text-center p-8 text-gray-500 card">No transactions found for the selected filters.</div>;
  }

  const getTransactionTypeColor = (type: string) => {
    switch (type) {
        case 'BUY':
        case 'ESPP_PURCHASE':
        case 'RSU_VEST':
            return 'text-green-600';
        case 'SELL':
            return 'text-red-600';
        default:
            return 'text-gray-600';
    }
    };

  return (
    <div className="card overflow-x-auto">
      <table className="table-auto w-full">
        <thead className="bg-gray-100">
          <tr>
            <th className="p-3 text-left text-sm font-semibold text-gray-600">Date</th>
            <th className="p-3 text-left text-sm font-semibold text-gray-600">Ticker</th>
            <th className="p-3 text-left text-sm font-semibold text-gray-600">Asset Name</th>
            <th className="p-3 text-left text-sm font-semibold text-gray-600">Type</th>
            <th className="p-3 text-right text-sm font-semibold text-gray-600">Quantity</th>
            <th className="p-3 text-right text-sm font-semibold text-gray-600">Price/Unit</th>
            <th className="p-3 text-right text-sm font-semibold text-gray-600">Total Value</th>
            <th className="p-3 text-center text-sm font-semibold text-gray-600">Actions</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((tx) => (
            <tr key={tx.id} className="border-b hover:bg-gray-50">
              <td className="p-3 text-sm">{formatDate(tx.transaction_date)}</td>
              <td className="p-3 text-sm font-mono">{tx.asset.ticker_symbol}</td>
              <td className="p-3 text-sm">{tx.asset.name}</td>
              <td className={`p-3 text-sm font-semibold ${getTransactionTypeColor(tx.transaction_type)}`}>
                <div className="flex items-center">
                    {tx.transaction_type.replace('_', ' ')}
                    {tx.details && (
                        <Tooltip content={<TransactionDetailTooltip details={tx.details} />}>
                            <InformationCircleIcon className="h-5 w-5 text-gray-400 ml-2" />
                        </Tooltip>
                    )}
                </div>
              </td>
              <td className="p-3 text-sm text-right">{Number(tx.quantity).toLocaleString()}</td>
              <td className="p-3 text-sm text-right">{formatCurrency(tx.price_per_unit)}</td>
              <td className="p-3 text-sm text-right">{formatCurrency(Number(tx.price_per_unit) * Number(tx.quantity))}</td>
              <td className="p-3 text-center"><div className="flex justify-center space-x-2"><button onClick={() => onEdit(tx)} className="btn btn-secondary btn-sm">Edit</button><button onClick={() => onDelete(tx)} className="btn btn-danger btn-sm">Delete</button></div></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TransactionHistoryTable;

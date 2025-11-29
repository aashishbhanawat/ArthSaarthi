import React from 'react';
import { Transaction } from '../../types/portfolio';
import { formatCurrency, formatDate } from '../../utils/formatting';

interface TransactionHistoryTableProps {
  transactions: Transaction[];
  onEdit: (transaction: Transaction) => void;
  onDelete: (transaction: Transaction) => void;
}

const getTypeColor = (type: string) => {
    switch(type) {
        case 'BUY': return 'text-green-600';
        case 'SELL': return 'text-red-600';
        case 'RSU_VEST': return 'text-purple-600';
        case 'ESPP_PURCHASE': return 'text-blue-600';
        case 'DIVIDEND': return 'text-green-500';
        case 'SPLIT': return 'text-orange-500';
        case 'BONUS': return 'text-green-500';
        default: return 'text-gray-600';
    }
};

const TransactionHistoryTable: React.FC<TransactionHistoryTableProps> = ({ transactions, onEdit, onDelete }) => {
  if (transactions.length === 0) {
    return <div className="text-center p-8 text-gray-500 card">No transactions found for the selected filters.</div>;
  }

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
              <td className={`p-3 text-sm font-semibold ${getTypeColor(tx.transaction_type)}`}>
                  {tx.transaction_type}
                  {tx.details && (
                      <span className="ml-1 text-gray-400 cursor-help" title={JSON.stringify(tx.details, null, 2)}>
                          (i)
                      </span>
                  )}
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

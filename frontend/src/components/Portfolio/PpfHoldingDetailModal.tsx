import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline';
import React from 'react';

import { useAssetAnalytics, useAssetTransactions } from '../../hooks/usePortfolios';
import { Holding } from '../../types/holding';
import { Transaction } from '../../types/portfolio';
import { formatCurrency, formatDate } from '../../utils/formatting';

interface PpfHoldingDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEdit: (transaction: Transaction) => void;
  onDelete: (transaction: Transaction) => void;
  holding: Holding;
  portfolioId: string;
}

const PpfHoldingDetailModal: React.FC<PpfHoldingDetailModalProps> = ({
  isOpen,
  onClose,
  onEdit,
  onDelete,
  holding,
  portfolioId,
}) => {
  const {
    data: transactions,
    isLoading,
    isError,
  } = useAssetTransactions(portfolioId, holding.asset_id);

  const { data: analytics, isLoading: isLoadingAnalytics } = useAssetAnalytics(portfolioId, holding.asset_id);

  if (!isOpen) return null;

  const contributions = transactions?.filter(tx => tx.transaction_type === 'CONTRIBUTION') || [];
  const interestCredits = transactions?.filter(tx => tx.transaction_type === 'INTEREST_CREDIT') || [];

  const totalContributions = contributions.reduce((acc, tx) => acc + parseFloat(tx.quantity), 0);
  const totalInterest = interestCredits.reduce((acc, tx) => acc + parseFloat(tx.quantity), 0);

  const sortedTransactions = [...(transactions || [])].sort(
    (a, b) => new Date(a.transaction_date).getTime() - new Date(b.transaction_date).getTime()
  );

  let runningBalance = 0;
  const transactionsWithBalance = sortedTransactions.map(tx => {
    const amount = parseFloat(tx.quantity);
    runningBalance += amount;
    return { ...tx, amount, runningBalance };
  });

  const reversedTransactions = [...transactionsWithBalance].reverse();

  const renderContent = () => {
    if (isLoading) {
      return <p className="dark:text-gray-300">Loading transactions...</p>;
    }
    if (isError) {
      return <p className="text-red-500">Error fetching transaction details.</p>;
    }
    if (!transactions) {
      return <p className="dark:text-gray-300">No transactions found for this holding.</p>;
    }

    return (
      <>
        {/* Summary Cards */}
        <div
          className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6 bg-gray-50 dark:bg-gray-700 p-4 rounded-lg"
          data-testid="ppf-summary-cards"
        >
          <div data-testid="summary-total-contributions">
            <p className="text-sm text-gray-500 dark:text-gray-400">Total Contributions</p>
            <p className="font-semibold dark:text-gray-100">{formatCurrency(totalContributions)}</p>
          </div>
          <div data-testid="summary-interest-earned">
            <p className="text-sm text-gray-500 dark:text-gray-400">Interest Earned</p>
            <p className="font-semibold text-green-600 dark:text-green-400">{formatCurrency(totalInterest)}</p>
          </div>
          <div data-testid="summary-current-value">
            <p className="text-sm text-gray-500 dark:text-gray-400">Current Value</p>
            <p className="font-semibold text-lg dark:text-gray-100">{formatCurrency(holding.current_value)}</p>
          </div>
          <div data-testid="summary-annualized-return">
            <p className="text-sm text-gray-500 dark:text-gray-400">Annualized Return</p>
            <p className="font-semibold dark:text-gray-100">
              {isLoadingAnalytics ? '...' : `${((analytics?.xirr_current ?? 0) * 100).toFixed(2)}%`}
            </p>
          </div>
          <div data-testid="summary-current-rate">
            <p className="text-sm text-gray-500 dark:text-gray-400">Current Rate</p>
            <p className="font-semibold dark:text-gray-100">{holding.interest_rate ? Number(holding.interest_rate).toFixed(2) : 'N/A'}%</p>
          </div>
        </div>

        {/* Transaction History Table */}
        <div className="overflow-y-auto max-h-96">
          <table className="table-auto w-full">
            <thead className="sticky top-0 bg-white dark:bg-gray-800 shadow-sm">
              <tr className="text-left text-gray-600 dark:text-gray-400 text-sm">
                <th className="p-2">Date</th>
                <th className="p-2">Description</th>
                <th className="p-2 text-right">Amount</th>
                <th className="p-2 text-right">Balance</th>
                <th className="p-2 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {reversedTransactions.map(tx => (
                <tr key={tx.id} className="border-t dark:border-gray-700">
                  <td className="p-2 dark:text-gray-200">{formatDate(tx.transaction_date)}</td>
                  <td className="p-2 font-semibold dark:text-gray-200">
                    {tx.transaction_type === 'CONTRIBUTION'
                      ? 'Contribution'
                      : `Interest Credit FY ${new Date(tx.transaction_date).getFullYear() - 1}-${new Date(
                        tx.transaction_date
                      ).getFullYear()}`}
                  </td>
                  <td className="p-2 text-right font-mono text-green-600 dark:text-green-400">
                    + {formatCurrency(tx.amount)}
                  </td>
                  <td className="p-2 text-right font-mono dark:text-gray-200">{formatCurrency(tx.runningBalance)}</td>
                  <td className="p-2 text-center">
                    {tx.transaction_type === 'CONTRIBUTION' ? (
                      <div className="flex items-center justify-center space-x-3">
                        <button
                          className="text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
                          title="Edit Transaction"
                          onClick={() => onEdit(tx)}
                        >
                          <PencilSquareIcon className="h-5 w-5" />
                        </button>
                        <button
                          className="text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
                          title="Delete Transaction"
                          onClick={() => onDelete(tx)}
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    ) : (
                      <span className="text-gray-400 dark:text-gray-500 italic text-sm">System</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </>
    );
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center transition-opacity ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
    >
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose}></div>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={`ppf-holding-detail-modal-title-${holding.asset_id}`}
        className="modal-content w-full max-w-3xl p-6 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl bg-white dark:bg-gray-800 z-10"
      >
        <div
          id={`ppf-holding-detail-modal-title-${holding.asset_id}`}
          className="flex justify-between items-center mb-4"
        >
          <div>
            <h2 className="text-2xl font-bold dark:text-gray-100">
              PPF Account: {holding.asset_name} ({holding.account_number})
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Opened on: {holding.opening_date ? formatDate(holding.opening_date) : 'N/A'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:hover:text-gray-200 dark:hover:bg-gray-700 rounded-full w-8 h-8 flex items-center justify-center transition-colors -mr-2 -mt-2"
          >
            <span className="text-2xl leading-none">&times;</span>
          </button>
        </div>
        {renderContent()}
        <div className="flex justify-end mt-6">
          <button onClick={onClose} className="btn btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default PpfHoldingDetailModal;
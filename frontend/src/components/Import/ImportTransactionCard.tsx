import React from 'react';
import { ParsedTransaction } from '../../types/import';
import { formatDate, formatCurrency } from '../../utils/formatting';

interface ImportTransactionCardProps {
    transaction: ParsedTransaction;
    isSelected: boolean;
    onToggleSelection: () => void;
    isDuplicate: boolean;
    isNeedsMapping: boolean;
    onMapTicker?: () => void;
}

const ImportTransactionCard: React.FC<ImportTransactionCardProps> = ({
    transaction,
    isSelected,
    onToggleSelection,
    isDuplicate,
    isNeedsMapping,
    onMapTicker
}) => {
    return (
        <div
            className={`card p-4 transition-all duration-200 border-l-4 ${isNeedsMapping ? 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/10' :
                isDuplicate ? 'border-l-warning bg-warning/5 dark:bg-warning/10' :
                    'border-l-success bg-white dark:bg-gray-800'
                } ${!isSelected && !isNeedsMapping ? 'opacity-70 grayscale-[0.3]' : 'shadow-md'} mb-3`}
        >
            <div className="flex items-start gap-3">
                {!isNeedsMapping && (
                    <div className="pt-1">
                        <input
                            type="checkbox"
                            className={`checkbox checkbox-sm ${isDuplicate ? 'checkbox-warning' : 'checkbox-success'}`}
                            checked={isSelected}
                            onChange={onToggleSelection}
                        />
                    </div>
                )}

                <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-2">
                        <div className="flex flex-wrap gap-2">
                            {isDuplicate ? (
                                <span className="badge badge-warning badge-xs">Duplicate</span>
                            ) : isNeedsMapping ? (
                                <span className="badge badge-info badge-xs text-white">Needs Mapping</span>
                            ) : (
                                <span className="badge badge-success badge-xs">New</span>
                            )}
                            <span className={`badge badge-xs ${transaction.transaction_type.toUpperCase() === 'BUY' ? 'badge-success' : 'badge-error'
                                }`}>
                                {transaction.transaction_type.toUpperCase()}
                            </span>
                        </div>
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                            {formatDate(transaction.transaction_date)}
                        </span>
                    </div>

                    <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate mb-1">
                        {transaction.ticker_symbol}
                    </h3>

                    <div className="grid grid-cols-2 gap-y-1 mt-2">
                        <div className="text-xs text-gray-500 dark:text-gray-400">Qty:</div>
                        <div className="text-xs font-semibold text-gray-900 dark:text-gray-100 text-right">
                            {transaction.quantity.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 4 })}
                        </div>

                        <div className="text-xs text-gray-500 dark:text-gray-400">Price/Unit:</div>
                        <div className="text-xs font-semibold text-gray-900 dark:text-gray-100 text-right">
                            {formatCurrency(transaction.price_per_unit)}
                        </div>

                        {transaction.fees > 0 && (
                            <>
                                <div className="text-xs text-gray-500 dark:text-gray-400">Fees:</div>
                                <div className="text-xs font-semibold text-gray-900 dark:text-gray-100 text-right text-error">
                                    {formatCurrency(transaction.fees)}
                                </div>
                            </>
                        )}
                    </div>

                    {isNeedsMapping && onMapTicker && (
                        <div className="mt-4 pt-3 border-t border-blue-200 dark:border-blue-800">
                            <button
                                className="btn btn-primary btn-sm w-full gap-2 shadow-sm"
                                onClick={onMapTicker}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                                </svg>
                                <span>Map Symbol</span>
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ImportTransactionCard;

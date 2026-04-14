import React from 'react';
import { ParsedTransaction } from '../../types/import';
import { formatCurrency, formatDate } from '../../utils/formatting';
import ImportTransactionCard from './ImportTransactionCard';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface MappingResolutionModalProps {
    isOpen: boolean;
    onClose: () => void;
    transactions: ParsedTransaction[];
    onMapTicker: (ticker: string) => void;
}

const MappingResolutionModal: React.FC<MappingResolutionModalProps> = ({
    isOpen,
    onClose,
    transactions,
    onMapTicker,
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose}></div>
            <div className="modal-content relative w-full max-w-4xl max-h-[90vh] flex flex-col pt-safe bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden border border-gray-200 dark:border-gray-700">
                <div className="flex justify-between items-center p-6 border-b border-gray-100 dark:border-gray-700">
                    <div>
                        <h2 className="text-xl font-bold dark:text-gray-100">Resolve Symbol Mappings</h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            The following {transactions.length} symbols need to be mapped before importing.
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
                    >
                        <XMarkIcon className="h-6 w-6" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6">
                    {/* Desktop view */}
                    <div className="hidden md:block overflow-x-auto">
                        <table className="table-auto w-full">
                            <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0">
                                <tr>
                                    <th className="p-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date</th>
                                    <th className="p-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Ticker</th>
                                    <th className="p-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
                                    <th className="p-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Quantity</th>
                                    <th className="p-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Price/Unit</th>
                                    <th className="p-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {transactions.map((tx, index) => (
                                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                        <td className="p-3 whitespace-nowrap dark:text-gray-300">{formatDate(tx.transaction_date)}</td>
                                        <td className="p-3 font-medium max-w-xs break-words dark:text-gray-200">{tx.ticker_symbol}</td>
                                        <td className="p-3 whitespace-nowrap">
                                            <span className={`badge ${tx.transaction_type.toUpperCase() === 'BUY' ? 'badge-success' : 'badge-error'}`}>
                                                {tx.transaction_type.toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="p-3 whitespace-nowrap text-right dark:text-gray-300">{tx.quantity}</td>
                                        <td className="p-3 whitespace-nowrap text-right dark:text-gray-300">{formatCurrency(tx.price_per_unit)}</td>
                                        <td className="p-3 whitespace-nowrap text-right">
                                            <button
                                                className="btn btn-xs btn-primary shadow-sm"
                                                onClick={() => onMapTicker(tx.ticker_symbol)}
                                            >
                                                Map Symbol
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Mobile view */}
                    <div className="md:hidden space-y-4">
                        {transactions.map((tx, index) => (
                            <ImportTransactionCard
                                key={index}
                                transaction={tx}
                                isSelected={false}
                                onToggleSelection={() => { }}
                                isDuplicate={false}
                                isNeedsMapping={true}
                                onMapTicker={() => onMapTicker(tx.ticker_symbol)}
                            />
                        ))}
                    </div>
                </div>

                <div className="p-6 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex justify-end">
                    <button onClick={onClose} className="btn btn-secondary">
                        Forward to Preview
                    </button>
                </div>
            </div>
        </div>
    );
};

export default MappingResolutionModal;

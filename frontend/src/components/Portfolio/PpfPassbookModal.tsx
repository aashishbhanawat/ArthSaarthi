import React from 'react';
import { Holding } from '../../types/holding';
import { Transaction } from '../../types/transaction';
import { formatCurrency, formatDate } from '../../utils/formatting';

interface PpfPassbookModalProps {
    holding: Holding;
    transactions: Transaction[];
    onClose: () => void;
}

const PpfPassbookModal: React.FC<PpfPassbookModalProps> = ({ holding, transactions, onClose }) => {
    const sortedTransactions = [...transactions].sort((a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime());

    return (
        <div className="modal-overlay z-30" onClick={onClose}>
            <div className="modal-content w-11/12 md:w-3/4 lg:max-w-4xl" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <div>
                        <h2 className="text-2xl font-bold">PPF Account: {holding.asset_name} ({holding.account_number})</h2>
                        <p className="text-sm text-gray-500">Opened on: {formatDate(holding.opening_date)}</p>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-800 text-2xl font-bold">&times;</button>
                </div>
                <div className="p-6 max-h-[70vh] overflow-y-auto">
                    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 text-center mb-6">
                        <div className="p-3 bg-gray-100 rounded-lg">
                            <h4 className="text-sm text-gray-600">Total Contributions</h4>
                            <p className="text-xl font-bold">{formatCurrency(holding.total_invested_amount)}</p>
                        </div>
                        <div className="p-3 bg-gray-100 rounded-lg">
                            <h4 className="text-sm text-gray-600">Interest Earned</h4>
                            <p className="text-xl font-bold text-green-600">{formatCurrency(holding.unrealized_pnl)}</p>
                        </div>
                        <div className="p-3 bg-gray-100 rounded-lg">
                            <h4 className="text-sm text-gray-600">Current Balance</h4>
                            <p className="text-xl font-bold">{formatCurrency(holding.current_value)}</p>
                        </div>
                        <div className="p-3 bg-gray-100 rounded-lg">
                            <h4 className="text-sm text-gray-600">Annualized Ret.</h4>
                            <p className="text-xl font-bold">{holding.unrealized_pnl_percentage.toFixed(2)}%</p>
                        </div>
                        <div className="p-3 bg-gray-100 rounded-lg">
                            <h4 className="text-sm text-gray-600">Current Rate</h4>
                            <p className="text-xl font-bold">{holding.interest_rate?.toFixed(2)}%</p>
                        </div>
                    </div>

                    <h3 className="text-xl font-semibold mb-4">Transaction History</h3>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Balance</th>
                                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {sortedTransactions.map((tx) => (
                                    <tr key={tx.id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">{formatDate(tx.transaction_date)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">{tx.transaction_type === 'INTEREST_CREDIT' ? `Interest Credit FY` : 'Contribution'}</td>
                                        <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${tx.transaction_type === 'INTEREST_CREDIT' ? 'text-green-600' : ''}`}>
                                            + {formatCurrency(tx.quantity)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right">{/* Balance calculation needed */}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                                            {tx.transaction_type === 'CONTRIBUTION' ? (
                                                <button className="text-gray-400 hover:text-gray-600">⚙️</button>
                                            ) : (
                                                <span className="text-gray-400">System</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PpfPassbookModal;

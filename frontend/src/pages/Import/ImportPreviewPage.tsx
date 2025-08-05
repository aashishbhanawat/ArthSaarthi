import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useImportSession, useParsedTransactions, useCommitImportSession } from '../../hooks/useImport';
import { formatCurrency, formatDate } from '../../utils/formatting';

const ImportPreviewPage: React.FC = () => {
    const { sessionId } = useParams<{ sessionId: string }>();
    const navigate = useNavigate();

    if (!sessionId) {
        return <div className="alert alert-error">No session ID provided.</div>;
    }

    const { data: session, isLoading: isLoadingSession, error: sessionError } = useImportSession(sessionId);
    const { data: transactions, isLoading: isLoadingTransactions, error: transactionsError } = useParsedTransactions(sessionId);
    const commitMutation = useCommitImportSession();

    useEffect(() => {
        if (commitMutation.isSuccess && session && commitMutation.data) {
            // Only redirect if the commit was actually successful and not just a skip
            if (commitMutation.data.msg.startsWith("Successfully committed")) {
                setTimeout(() => {
                    navigate(`/portfolios/${session.portfolio_id}`);
                }, 2000);
            }
        }
    }, [commitMutation.isSuccess, commitMutation.data, session, navigate]);

    if (isLoadingSession || isLoadingTransactions) {
        return <div>Loading import preview...</div>;
    }

    if (sessionError || transactionsError) {
        return (
            <div className="alert alert-error">
                Error loading import data: {sessionError?.message || transactionsError?.message}
            </div>
        );
    }

    if (!session || !transactions) {
        return <div className="alert">No data available for this import session.</div>;
    }

    const handleCommit = () => {
        if (sessionId && session.portfolio_id) {
            commitMutation.mutate({ sessionId, portfolioId: session.portfolio_id });
        }
    };

    const handleCancel = () => {
        // A real implementation might call a DELETE endpoint to clean up the session.
        // For now, just navigate back to the upload page.
        navigate('/import');
    };

    const renderStatusBadge = (status: string) => {
        const baseClasses = 'badge';
        switch (status) {
            case 'PARSED': return `${baseClasses} badge-info`;
            case 'COMPLETED': return `${baseClasses} badge-success`;
            case 'FAILED': return `${baseClasses} badge-error`;
            default: return `${baseClasses} badge-ghost`;
        }
    };

    const canCommit = session.status === 'PARSED';

    return (
        <div>
            <div className="flex justify-between items-center mb-4">
                <h1 className="text-3xl font-bold text-gray-800">Import Preview</h1>
                <span className={renderStatusBadge(session.status)}>{session.status}</span>
            </div>
            <p className="text-gray-600 mb-8">
                Review the transactions parsed from <span className="font-semibold">{session.file_name}</span> for portfolio <span className="font-semibold">{session.portfolio.name}</span>.
            </p>

            <div className="card">
                <div className="p-4 bg-blue-50 border-b border-blue-200 rounded-t-lg">
                    <h3 className="font-semibold text-blue-800">Import Summary</h3>
                    <p className="text-sm text-blue-700 mt-1">
                        Found <span className="font-bold">{transactions.length}</span> transactions to be added. Please review them before committing.
                    </p>
                </div>
                <div className="overflow-x-auto p-4">
                    <table className="table w-full table-zebra">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ticker</th>
                                <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                                <th className="p-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                                <th className="p-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Price/Unit</th>
                                <th className="p-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Fees</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {transactions.map((tx, index) => (
                                <tr key={index} className="hover:bg-gray-50">
                                    <td className="p-3 whitespace-nowrap">{formatDate(tx.transaction_date)}</td>
                                    <td className="p-3 whitespace-nowrap font-medium text-gray-900">{tx.ticker_symbol}</td>
                                    <td className="p-3 whitespace-nowrap">
                                        <span className={`badge ${tx.transaction_type.toUpperCase() === 'BUY' ? 'badge-success' : 'badge-error'}`}>
                                            {tx.transaction_type.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="p-3 whitespace-nowrap text-right">{tx.quantity}</td>
                                    <td className="p-3 whitespace-nowrap text-right">{formatCurrency(tx.price_per_unit)}</td>
                                    <td className="p-3 whitespace-nowrap text-right">{formatCurrency(tx.fees)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="mt-8 flex justify-end gap-4">
                <button onClick={handleCancel} className="btn btn-secondary" disabled={commitMutation.isPending || commitMutation.isSuccess}>
                    Cancel
                </button>
                <button onClick={handleCommit} className="btn btn-primary" disabled={!canCommit || commitMutation.isPending || commitMutation.isSuccess}>
                    {commitMutation.isPending ? 'Committing...' : 'Commit Transactions'}
                </button>
            </div>

            {commitMutation.isSuccess && (
                <div className={`alert ${commitMutation.data?.msg.startsWith("Successfully committed") ? 'alert-success' : 'alert-warning'} mt-4`}>
                    {commitMutation.data?.msg}
                    {commitMutation.data?.msg.startsWith("Successfully committed") && (
                        " Redirecting to portfolio..."
                    )}
                </div>
            )}
            {commitMutation.isError && (
                <div className="alert alert-error mt-4">
                    Error committing transactions: {
                        (commitMutation.error as any)?.response?.data?.detail || commitMutation.error.message
                    }
                </div>
            )}
        </div>
    );
};

export default ImportPreviewPage;
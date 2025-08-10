import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useImportSession, useImportSessionPreview, useCommitImportSession } from '../../hooks/useImport';
import { formatCurrency, formatDate } from '../../utils/formatting';
import { ParsedTransaction } from '../../types/import';

const ImportPreviewPage: React.FC = () => {
    const { sessionId } = useParams<{ sessionId: string }>();
    const navigate = useNavigate();

    // State for managing which transactions are selected for commit
    const [selectedTransactions, setSelectedTransactions] = useState<Set<number>>(new Set());

    const { data: session, isLoading: isLoadingSession, error: sessionError } = useImportSession(sessionId);
    const { data: previewData, isLoading: isLoadingPreview, error: previewError } = useImportSessionPreview(sessionId);
    const commitMutation = useCommitImportSession();

    const transactions = useMemo(() => {
        if (!previewData) return { valid_new: [], duplicates: [], invalid: [] };
        return previewData;
    }, [previewData]);

    // When data loads, pre-select all valid new transactions
    useEffect(() => {
        if (transactions.valid_new) {
            const initialSelection = new Set(transactions.valid_new.map((_, index) => index));
            setSelectedTransactions(initialSelection);
        }
    }, [transactions.valid_new]);

    useEffect(() => {
        if (commitMutation.isSuccess && session && commitMutation.data) {
            if (commitMutation.data.msg.startsWith("Successfully committed")) {
                setTimeout(() => {
                    navigate(`/portfolios/${session.portfolio_id}`);
                }, 2000);
            }
        }
    }, [commitMutation.isSuccess, commitMutation.data, session, navigate]);

    if (!sessionId) return <div className="alert alert-error">No session ID provided.</div>;
    if (isLoadingSession || isLoadingPreview) return <div>Loading import preview...</div>;
    if (sessionError || previewError) return <div className="alert alert-error">Error loading import data: {sessionError?.message || previewError?.message}</div>;
    if (!session || !previewData) return <div className="alert">No data available for this import session.</div>;

    const handleToggleSelection = (index: number) => {
        setSelectedTransactions(prevSelection => {
            const newSelection = new Set(prevSelection);
            if (newSelection.has(index)) {
                newSelection.delete(index);
            } else {
                newSelection.add(index);
            }
            return newSelection;
        });
    };

    const handleToggleSelectAll = () => {
        if (selectedTransactions.size === transactions.valid_new.length) {
            setSelectedTransactions(new Set()); // Deselect all
        } else {
            const allIndices = new Set(transactions.valid_new.map((_, index) => index));
            setSelectedTransactions(allIndices); // Select all
        }
    };

    const handleCommit = () => {
        if (sessionId && session.portfolio_id) {
            const transactions_to_commit = transactions.valid_new.filter((_, index) => selectedTransactions.has(index));
            commitMutation.mutate({
                sessionId,
                portfolioId: session.portfolio_id,
                commitPayload: {
                    transactions_to_commit,
                    aliases_to_create: [], // Alias creation UI not implemented yet
                },
            });
        }
    };

    const handleCancel = () => navigate('/import');

    const renderStatusBadge = (status: string) => {
        const baseClasses = 'badge';
        switch (status) {
            case 'PARSED': return `${baseClasses} badge-info`;
            case 'COMPLETED': return `${baseClasses} badge-success`;
            case 'FAILED': return `${baseClasses} badge-error`;
            default: return `${baseClasses} badge-ghost`;
        }
    };

    const canCommit = session.status === 'PARSED' && selectedTransactions.size > 0;

    const TransactionTable = ({ transactions, selectable = false }: { transactions: ParsedTransaction[], selectable?: boolean }) => (
        <div className="overflow-x-auto">
            <table className="table w-full table-zebra">
                <thead className="bg-gray-50">
                    <tr>
                        {selectable && (
                            <th className="p-3 w-12"><input type="checkbox" className="checkbox" checked={selectedTransactions.size === transactions.length && transactions.length > 0} onChange={handleToggleSelectAll} /></th>
                        )}
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
                            {selectable && (
                                <td className="p-3"><input type="checkbox" className="checkbox" checked={selectedTransactions.has(index)} onChange={() => handleToggleSelection(index)} /></td>
                            )}
                            <td className="p-3 whitespace-nowrap">{formatDate(tx.transaction_date)}</td>
                            <td className="p-3 whitespace-nowrap font-medium text-gray-900">{tx.ticker_symbol}</td>
                            <td className="p-3 whitespace-nowrap"><span className={`badge ${tx.transaction_type.toUpperCase() === 'BUY' ? 'badge-success' : 'badge-error'}`}>{tx.transaction_type.toUpperCase()}</span></td>
                            <td className="p-3 whitespace-nowrap text-right">{tx.quantity}</td>
                            <td className="p-3 whitespace-nowrap text-right">{formatCurrency(tx.price_per_unit)}</td>
                            <td className="p-3 whitespace-nowrap text-right">{formatCurrency(tx.fees)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );

    // TODO: Add UI for invalid transactions

    return (
        <div>
            <div className="flex justify-between items-center mb-4">
                <h1 className="text-3xl font-bold text-gray-800">Import Preview</h1>
                <span className={renderStatusBadge(session.status)}>{session.status}</span>
            </div>
            <p className="text-gray-600 mb-8">Review the transactions parsed from <span className="font-semibold">{session.file_name}</span> for portfolio <span className="font-semibold">{session.portfolio.name}</span>.</p>

            <div className="space-y-6">
                {/* New Transactions */}
                <div className="card">
                    <details className="collapse collapse-arrow bg-base-200" open>
                        <summary className="collapse-title text-xl font-medium">
                            New Transactions ({transactions.valid_new.length})
                        </summary>
                        <div className="collapse-content">
                            {transactions.valid_new.length > 0 ? <TransactionTable transactions={transactions.valid_new} selectable={true} /> : <p className="p-4 text-gray-500">No new transactions to import.</p>}
                        </div>
                    </details>
                </div>

                {/* Duplicate Transactions */}
                {transactions.duplicates.length > 0 && (
                    <div className="card">
                        <details className="collapse collapse-arrow bg-base-200">
                            <summary className="collapse-title text-xl font-medium">
                                Potential Duplicates ({transactions.duplicates.length})
                            </summary>
                            <div className="collapse-content">
                                <TransactionTable transactions={transactions.duplicates} />
                            </div>
                        </details>
                    </div>
                )}
            </div>

            <div className="mt-8 flex justify-end gap-4">
                <button onClick={handleCancel} className="btn btn-secondary" disabled={commitMutation.isPending || commitMutation.isSuccess}>Cancel</button>
                <button onClick={handleCommit} className="btn btn-primary" disabled={!canCommit || commitMutation.isPending || commitMutation.isSuccess}>
                    {commitMutation.isPending ? 'Committing...' : `Commit ${selectedTransactions.size} Transactions`}
                </button>
            </div>

            {commitMutation.isSuccess && (
                <div className={`alert ${commitMutation.data?.msg.startsWith("Successfully committed") ? 'alert-success' : 'alert-warning'} mt-4`}>
                    {commitMutation.data?.msg}
                    {commitMutation.data?.msg.startsWith("Successfully committed") && " Redirecting to portfolio..."}
                </div>
            )}
            {commitMutation.isError && (
                <div className="alert alert-error mt-4">
                    Error committing transactions: {((commitMutation.error as { response?: { data?: { detail?: string } } }).response?.data?.detail) || (commitMutation.error as Error).message}
                </div>
            )}
        </div>
    );
};

export default ImportPreviewPage;
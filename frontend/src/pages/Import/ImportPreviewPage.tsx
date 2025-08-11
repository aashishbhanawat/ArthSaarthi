import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useImportSession, useImportSessionPreview, useCommitImportSession } from '../../hooks/useImport';
import { formatCurrency, formatDate } from '../../utils/formatting';
import { ParsedTransaction } from '../../types/import';

const ImportPreviewPage: React.FC = () => {
    const { sessionId } = useParams<{ sessionId: string }>();
    const navigate = useNavigate();

    // State for managing which transactions are selected for commit
    const [selectedTransactionIndices, setSelectedTransactionIndices] = useState<Set<number>>(new Set());

    const { data: session, isLoading: isLoadingSession, error: sessionError } = useImportSession(sessionId);
    const { data: previewData, isLoading: isLoadingPreview, error: previewError } = useImportSessionPreview(sessionId);
    const commitMutation = useCommitImportSession();

    const allSelectableTransactions = useMemo(() => {
        if (!previewData) return [];
        return [...previewData.valid_new, ...previewData.duplicates];
    }, [previewData]);

    // When data loads, pre-select all valid new transactions
    useEffect(() => {
        if (previewData?.valid_new) {
            const initialSelection = new Set(previewData.valid_new.map((_, index) => index));
            setSelectedTransactionIndices(initialSelection);
        }
    }, [previewData?.valid_new]);

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

    const handleToggleSelection = (transactionIndex: number) => {
        setSelectedTransactionIndices(prevSelection => {
            const newSelection = new Set(prevSelection);
            if (newSelection.has(transactionIndex)) {
                newSelection.delete(transactionIndex);
            } else {
                newSelection.add(transactionIndex);
            }
            return newSelection;
        });
    };

    const handleToggleSelectAll = () => {
        if (selectedTransactionIndices.size === allSelectableTransactions.length) {
            setSelectedTransactionIndices(new Set()); // Deselect all
        } else {
            const allIndices = new Set(allSelectableTransactions.map((_, index) => index));
            setSelectedTransactionIndices(allIndices); // Select all
        }
    };

    const handleCommit = () => {
        if (sessionId && session.portfolio_id) {
            const transactions_to_commit = allSelectableTransactions.filter((_, index) => selectedTransactionIndices.has(index));
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

    const canCommit = session.status === 'PARSED' && selectedTransactionIndices.size > 0;

    const TransactionTable = ({ transactions, selectable = false, isDuplicate = false, offset = 0 }: { transactions: ParsedTransaction[], selectable?: boolean, isDuplicate?: boolean, offset?: number }) => (
        <table className="table-auto w-full">
            <thead className="bg-gray-50">
                <tr>
                    {selectable && (
                        <th className="p-3 w-12"><input type="checkbox" className="checkbox" checked={selectedTransactionIndices.size === allSelectableTransactions.length && allSelectableTransactions.length > 0} onChange={handleToggleSelectAll} /></th>
                    )}
                    <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ticker</th>
                    <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="p-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                    <th className="p-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Price/Unit</th>
                    <th className="p-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Fees</th>
                </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200 text-gray-900">
                {transactions.map((tx, index) => {
                    const overallIndex = offset + index;
                    return (
                        <tr key={overallIndex} className="hover:bg-gray-50">
                            {selectable && (
                                <td className="p-3"><input type="checkbox" className="checkbox" checked={selectedTransactionIndices.has(overallIndex)} onChange={() => handleToggleSelection(overallIndex)} /></td>
                            )}
                            <td className="p-3 whitespace-nowrap">{isDuplicate ? <span className="badge badge-warning">Duplicate</span> : <span className="badge badge-success">New</span>}</td>
                            <td className="p-3 whitespace-nowrap">{formatDate(tx.transaction_date)}</td>
                            <td className="p-3 whitespace-nowrap font-medium">{tx.ticker_symbol}</td>
                            <td className="p-3 whitespace-nowrap"><span className={`badge ${tx.transaction_type.toUpperCase() === 'BUY' ? 'badge-success' : 'badge-error'}`}>{tx.transaction_type.toUpperCase()}</span></td>
                            <td className="p-3 whitespace-nowrap text-right">{tx.quantity}</td>
                            <td className="p-3 whitespace-nowrap text-right">{formatCurrency(tx.price_per_unit)}</td>
                            <td className="p-3 whitespace-nowrap text-right">{formatCurrency(tx.fees)}</td>
                        </tr>
                    )
                })}
            </tbody>
        </table>
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
                <div className="card p-4 sm:p-6">
                    <h2 className="text-xl font-medium mb-4">
                        New Transactions ({previewData.valid_new.length})
                    </h2>
                    <div className="overflow-x-auto">
                        {previewData.valid_new.length > 0 ? <TransactionTable transactions={previewData.valid_new} selectable={true} /> : <p className="text-center text-gray-500 py-4">No new transactions to import.</p>}
                    </div>
                </div>

                {/* Duplicate Transactions */}
                {previewData.duplicates.length > 0 && (
                    <div className="card p-4 sm:p-6">
                        <h2 className="text-xl font-medium mb-4">
                            Potential Duplicates ({previewData.duplicates.length})
                        </h2>
                        <p className="text-sm text-gray-500 mb-4">These transactions seem to already exist in this portfolio. Select them if you want to import them anyway.</p>
                        <div className="overflow-x-auto">
                            <TransactionTable transactions={previewData.duplicates} selectable={true} isDuplicate={true} offset={previewData.valid_new.length} />
                        </div>
                    </div>
                )}
            </div>

            <div className="mt-8 flex justify-end gap-4">
                <button onClick={handleCancel} className="btn btn-secondary" disabled={commitMutation.isPending || commitMutation.isSuccess}>Cancel</button>
                <button onClick={handleCommit} className="btn btn-primary" disabled={!canCommit || commitMutation.isPending || commitMutation.isSuccess}>
                    {commitMutation.isPending ? 'Committing...' : `Commit ${selectedTransactionIndices.size} Transactions`}
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
import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useImportSession, useImportSessionPreview, useCommitImportSession } from '../../hooks/useImport';
import { formatCurrency, formatDate } from '../../utils/formatting';
import { ParsedTransaction, AssetAliasCreate } from '../../types/import';
import AssetAliasMappingModal from '../../components/modals/AssetAliasMappingModal';
import ImportTransactionCard from '../../components/Import/ImportTransactionCard';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const ImportPreviewPage: React.FC = () => {
    const { sessionId } = useParams<{ sessionId: string }>();
    const navigate = useNavigate();

    // State for managing which transactions are selected for commit
    const [selectedTransactionIndices, setSelectedTransactionIndices] = useState<Set<number>>(new Set());
    const [aliasesToCreate, setAliasesToCreate] = useState<AssetAliasCreate[]>([]);
    const [isAliasModalOpen, setAliasModalOpen] = useState(false);
    const [tickerToMap, setTickerToMap] = useState<string | null>(null);


    const { data: session, isLoading: isLoadingSession, error: sessionError } = useImportSession(sessionId!);
    const { data: previewData, isLoading: isLoadingPreview, error: previewError } = useImportSessionPreview(sessionId!, aliasesToCreate);
    const commitMutation = useCommitImportSession();

    const allSelectableTransactions = useMemo(() => {
        if (!previewData) return [];
        return [...previewData.valid_new, ...previewData.duplicates];
    }, [previewData]);

    // When data loads, pre-select all valid new transactions
    useEffect(() => {
        if (previewData?.valid_new) {
            // Performance: Using .keys() to create a Set of indices avoids intermediate array creation overhead
            const initialSelection = new Set(previewData.valid_new.keys());
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
            // Performance: Using .keys() is faster and uses less memory than .map() for extracting array indices
            const allIndices = new Set(allSelectableTransactions.keys());
            setSelectedTransactionIndices(allIndices); // Select all
        }
    };

    const handleOpenAliasModal = (ticker: string) => {
        setTickerToMap(ticker);
        setAliasModalOpen(true);
    };

    const handleCloseAliasModal = () => {
        setTickerToMap(null);
        setAliasModalOpen(false);
    };

    const handleAliasCreated = (alias: AssetAliasCreate) => {
        // Update the list of pending aliases. React Query will automatically refetch the preview
        // because `aliasesToCreate` is now part of the query key for `useImportSessionPreview`.
        setAliasesToCreate(prev => [...prev.filter(a => a.alias_symbol !== alias.alias_symbol), alias]);
    };

    const handleCommit = () => {
        if (sessionId && session.portfolio_id) {
            const transactions_to_commit = allSelectableTransactions.filter((_, index) => selectedTransactionIndices.has(index));
            commitMutation.mutate({
                sessionId,
                portfolioId: session.portfolio_id,
                commitPayload: {
                    transactions_to_commit,
                    aliases_to_create: aliasesToCreate,
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
        <>
            {/* Desktop Table */}
            <div className="hidden md:block overflow-x-auto">
                <table className="table-auto w-full">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                            {selectable && (
                                <th className="p-3 w-12"><input type="checkbox" className="checkbox" checked={selectedTransactionIndices.size === allSelectableTransactions.length && allSelectableTransactions.length > 0} onChange={handleToggleSelectAll} /></th>
                            )}
                            <th className="p-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
                            <th className="p-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Date</th>
                            <th className="p-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Ticker</th>
                            <th className="p-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Type</th>
                            <th className="p-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                            <th className="p-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Price/Unit</th>
                            <th className="p-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Fees</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600 text-gray-900 dark:text-gray-200">
                        {transactions.map((tx, index) => {
                            const overallIndex = offset + index;
                            return (
                                <tr key={overallIndex} className="hover:bg-gray-50 dark:hover:bg-gray-700">
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
            </div>

            {/* Mobile Cards */}
            <div className="md:hidden space-y-1">
                {selectable && transactions.length > 0 && (
                    <div className="flex justify-between items-center px-1 mb-2">
                        <label className="flex items-center gap-2 cursor-pointer text-sm font-medium text-gray-600 dark:text-gray-400">
                            <input
                                type="checkbox"
                                className="checkbox checkbox-xs"
                                checked={selectedTransactionIndices.size === allSelectableTransactions.length && allSelectableTransactions.length > 0}
                                onChange={handleToggleSelectAll}
                            />
                            Select All
                        </label>
                        <span className="text-xs text-gray-500">{selectedTransactionIndices.size} selected</span>
                    </div>
                )}
                {transactions.map((tx, index) => {
                    const overallIndex = offset + index;
                    return (
                        <ImportTransactionCard
                            key={overallIndex}
                            transaction={tx}
                            isSelected={selectedTransactionIndices.has(overallIndex)}
                            onToggleSelection={() => handleToggleSelection(overallIndex)}
                            isDuplicate={isDuplicate}
                            isNeedsMapping={false}
                        />
                    );
                })}
            </div>
        </>
    );

    const InvalidTransactionTable = ({ invalidRows }: { invalidRows: { row_data: Record<string, unknown>; error: string }[] }) => {
        return (
            <table className="table-auto w-full">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Original Data</th>
                        <th className="p-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Error</th>
                    </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600 text-gray-900 dark:text-gray-200">
                    {invalidRows.map((item, index) => (
                        <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                            <td className="p-3 text-xs text-gray-500 break-all">{JSON.stringify(item.row_data)}</td>
                            <td className="p-3 whitespace-nowrap"><span className="badge badge-error">{item.error}</span></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-4">
                <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">Import Preview</h1>
                <span className={renderStatusBadge(session.status)}>{session.status}</span>
            </div>
            <div className="mb-6">
                <p className="text-gray-600 dark:text-gray-400 mb-4">Review the transactions parsed from <span className="font-semibold text-gray-800 dark:text-gray-200">{session.file_name}</span> for portfolio <span className="font-semibold text-gray-800 dark:text-gray-200">{session.portfolio.name}</span>.</p>
                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800 p-4 rounded-lg">
                    <p className="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
                        <span className="font-bold">Important:</span> Please cross-verify all imported transactions against your original statements. Some transactions may not be extractable due to PDF formatting issues. If any transactions are missing, please add them manually after import.
                    </p>
                </div>
            </div>

            <div className="space-y-6">
                {/* New Transactions */}
                <div className="card p-4 sm:p-6 shadow-sm border border-gray-100 dark:border-gray-800">
                    <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-gray-100">
                        New Transactions ({previewData.valid_new.length})
                    </h2>
                    {previewData.valid_new.length > 0 ? (
                        <TransactionTable transactions={previewData.valid_new} selectable={true} />
                    ) : (
                        <p className="text-center text-gray-500 py-4">No new transactions to import.</p>
                    )}
                </div>

                {/* Duplicate Transactions */}
                {previewData.duplicates.length > 0 && (
                    <div className="card p-4 sm:p-6 shadow-sm border border-gray-100 dark:border-gray-800">
                        <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-gray-100">
                            Potential Duplicates ({previewData.duplicates.length})
                        </h2>
                        <p className="text-sm text-gray-500 mb-4 italic">These transactions seem to already exist in this portfolio. Select them if you want to import them anyway.</p>
                        <TransactionTable transactions={previewData.duplicates} selectable={true} isDuplicate={true} offset={previewData.valid_new.length} />
                    </div>
                )}

                {/* Unrecognized Symbols (Needs Mapping) */}
                {previewData.needs_mapping.length > 0 && (
                    <div id="unrecognized-symbols" className="card p-4 sm:p-6 shadow-sm border border-blue-100 dark:border-blue-900 bg-blue-50/30 dark:bg-blue-900/10">
                        <h2 className="text-xl font-bold mb-4 text-blue-800 dark:text-blue-100 flex items-center gap-2">
                            <ExclamationTriangleIcon className="h-6 w-6" />
                            Transactions Needing Mapping ({previewData.needs_mapping.length})
                        </h2>
                        <p className="text-sm text-blue-700 dark:text-blue-300 mb-4 italic">
                            These transactions have unrecognized ticker symbols. Map them to an existing asset to include them in the import.
                        </p>

                        {/* Desktop Mapping Table */}
                        <div className="hidden md:block overflow-x-auto">
                            <table className="table-auto w-full">
                                <thead>
                                    <tr className="bg-blue-100 dark:bg-blue-900/50">
                                        <th className="p-3 text-left text-xs font-medium text-blue-800 dark:text-blue-200 uppercase tracking-wider">Date</th>
                                        <th className="p-3 text-left text-xs font-medium text-blue-800 dark:text-blue-200 uppercase tracking-wider">Ticker</th>
                                        <th className="p-3 text-left text-xs font-medium text-blue-800 dark:text-blue-200 uppercase tracking-wider">Type</th>
                                        <th className="p-3 text-right text-xs font-medium text-blue-800 dark:text-blue-200 uppercase tracking-wider">Quantity</th>
                                        <th className="p-3 text-right text-xs font-medium text-blue-800 dark:text-blue-200 uppercase tracking-wider">Price/Unit</th>
                                        <th className="p-3 text-right text-xs font-medium text-blue-800 dark:text-blue-200 uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                    {previewData.needs_mapping.map((tx, index) => (
                                        <tr key={`needs-map-${index}`} className="hover:bg-blue-50 dark:hover:bg-blue-900/20">
                                            <td className="p-3 whitespace-nowrap text-sm">{formatDate(tx.transaction_date)}</td>
                                            <td className="p-3 font-medium text-sm break-all">{tx.ticker_symbol}</td>
                                            <td className="p-3 whitespace-nowrap"><span className={`badge badge-xs ${tx.transaction_type.toUpperCase() === 'BUY' ? 'badge-success' : 'badge-error'}`}>{tx.transaction_type.toUpperCase()}</span></td>
                                            <td className="p-3 whitespace-nowrap text-right text-sm">{tx.quantity}</td>
                                            <td className="p-3 whitespace-nowrap text-right text-sm">{formatCurrency(tx.price_per_unit)}</td>
                                            <td className="p-3 whitespace-nowrap text-right">
                                                <button
                                                    onClick={() => handleOpenAliasModal(tx.ticker_symbol)}
                                                    className="btn btn-xs btn-primary shadow-sm"
                                                >
                                                    Map Symbol
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Mobile Mapping Cards */}
                        <div className="md:hidden space-y-3">
                            {previewData.needs_mapping.map((tx, index) => (
                                <ImportTransactionCard
                                    key={`needs-map-mobile-${index}`}
                                    transaction={tx}
                                    isSelected={false}
                                    onToggleSelection={() => { }}
                                    isDuplicate={false}
                                    isNeedsMapping={true}
                                    onMapTicker={() => handleOpenAliasModal(tx.ticker_symbol)}
                                />
                            ))}
                        </div>
                    </div>
                )}


                {/* Invalid Transactions */}
                {previewData.invalid.length > 0 && (
                    <div className="card p-4 sm:p-6 bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700">
                        <h2 className="text-xl font-medium mb-4 text-red-800 dark:text-red-300">
                            Invalid Transactions ({previewData.invalid.length})
                        </h2>
                        <p className="text-sm text-red-700 dark:text-red-400 mb-4">
                            These rows from the file could not be parsed and will be ignored. This is usually due to missing or malformed data.
                        </p>
                        <div className="overflow-x-auto">
                            <InvalidTransactionTable invalidRows={previewData.invalid} />
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

            {session && tickerToMap && (
                <AssetAliasMappingModal
                    isOpen={isAliasModalOpen}
                    onClose={handleCloseAliasModal}
                    unrecognizedTicker={tickerToMap}
                    portfolioId={session.portfolio_id}
                    source={session.source}
                    onAliasCreated={handleAliasCreated}
                />
            )}
        </div>
    );
};

export default ImportPreviewPage;
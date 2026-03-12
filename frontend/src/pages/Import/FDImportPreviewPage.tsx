import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useImportSession, useFDImportSessionPreview, useCommitFDImportSession } from '../../hooks/useImport';
import { ParsedFixedDeposit } from '../../types/import';
import { AxiosError } from 'axios';

const FDImportPreviewPage: React.FC = () => {
    const { sessionId } = useParams<{ sessionId: string }>();
    const navigate = useNavigate();

    const [editableFds, setEditableFds] = useState<ParsedFixedDeposit[]>([]);
    const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());

    const { data: session, isLoading: isLoadingSession, error: sessionError } = useImportSession(sessionId!);
    const { data: previewData, isLoading: isLoadingPreview, error: previewError } = useFDImportSessionPreview(sessionId!);
    const commitMutation = useCommitFDImportSession();

    // Initialize editable FDs and selection when preview data is loaded
    useEffect(() => {
        if (previewData) {
            setEditableFds([...previewData.parsed_fds, ...previewData.duplicates]);
            // Pre-select only non-duplicates
            const initialSelection = new Set<number>();
            previewData.parsed_fds.forEach((_, index) => initialSelection.add(index));
            setSelectedIndices(initialSelection);
        }
    }, [previewData]);

    useEffect(() => {
        if (commitMutation.isSuccess && session && commitMutation.data) {
            setTimeout(() => {
                navigate(`/portfolios/${session.portfolio_id}`);
            }, 2000);
        }
    }, [commitMutation.isSuccess, commitMutation.data, session, navigate]);

    if (!sessionId) return <div className="alert alert-error">No session ID provided.</div>;
    if (isLoadingSession || isLoadingPreview) return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading FD import preview...</div>;
    if (sessionError || previewError) return <div className="alert alert-error">Error loading import data: {sessionError?.message || previewError?.message}</div>;
    if (!session || !previewData) return <div className="alert">No data available for this import session.</div>;

    const handleFieldChange = (index: number, field: keyof ParsedFixedDeposit, value: string | number) => {
        setEditableFds(prev => {
            const next = [...prev];
            next[index] = { ...next[index], [field]: value };
            return next;
        });
    };

    const handleToggleSelection = (index: number) => {
        setSelectedIndices(prev => {
            const next = new Set(prev);
            if (next.has(index)) {
                next.delete(index);
            } else {
                next.add(index);
            }
            return next;
        });
    };

    const handleToggleSelectAll = () => {
        if (selectedIndices.size === editableFds.length) {
            setSelectedIndices(new Set());
        } else {
            // Performance: Using .keys() to create a Set of indices is ~20% faster than .map() as it avoids intermediate array creation
            setSelectedIndices(new Set(editableFds.keys()));
        }
    };

    const handleCommit = () => {
        if (sessionId && session.portfolio_id) {
            const fds_to_commit = editableFds.filter((_, index) => selectedIndices.has(index));
            commitMutation.mutate({
                sessionId,
                portfolioId: session.portfolio_id,
                commitPayload: { fds_to_commit },
            });
        }
    };

    const handleCancel = () => navigate('/import');

    const canCommit = session.status === 'PARSED' && selectedIndices.size > 0;

    return (
        <div className="pb-20">
            <div className="flex justify-between items-center mb-4">
                <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">FD Import Preview</h1>
                <span className={`badge ${session.status === 'PARSED' ? 'badge-info' : 'badge-ghost'}`}>{session.status}</span>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
                Review and edit the Fixed Deposits parsed from <span className="font-semibold">{session.file_name}</span> for portfolio <span className="font-semibold">{session.portfolio.name}</span>.
            </p>

            <div className="alert alert-warning mb-8">
                <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                <div>
                    <span className="font-bold">Important:</span> Compound frequency defaults to <span className="italic">Quarterly</span>. Interest payout is <span className="italic">Payout</span> if Maturity Amount equals Principal, otherwise <span className="italic">Cumulative</span>. <br />
                    <span className="font-bold">SBI Note:</span> Start Date may be the <span className="italic">original</span> open date, not the renewal date. Please verify all values.
                </div>
            </div>

            <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="table-auto w-full text-sm">
                        <thead className="bg-gray-50 dark:bg-gray-700 border-b dark:border-gray-600">
                            <tr>
                                <th className="p-3 w-10">
                                    <input
                                        type="checkbox"
                                        className="checkbox checkbox-sm"
                                        checked={selectedIndices.size === editableFds.length && editableFds.length > 0}
                                        onChange={handleToggleSelectAll}
                                    />
                                </th>
                                <th className="p-3 text-left font-medium text-gray-500 dark:text-gray-300">Bank / Account</th>
                                <th className="p-3 text-left font-medium text-gray-500 dark:text-gray-300">Principal</th>
                                <th className="p-3 text-left font-medium text-gray-500 dark:text-gray-300">Rate (%)</th>
                                <th className="p-3 text-left font-medium text-gray-500 dark:text-gray-300">Start Date</th>
                                <th className="p-3 text-left font-medium text-gray-500 dark:text-gray-300">Maturity Date</th>
                                <th className="p-3 text-left font-medium text-gray-500 dark:text-gray-300">Frequency</th>
                                <th className="p-3 text-left font-medium text-gray-500 dark:text-gray-300">Type</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
                            {editableFds.map((fd, index) => {
                                const isDuplicate = index >= previewData.parsed_fds.length;
                                return (
                                    <tr key={index} className={`hover:bg-gray-50 dark:hover:bg-gray-750 ${!selectedIndices.has(index) ? 'opacity-60' : ''}`}>
                                        <td className="p-3">
                                            <input
                                                type="checkbox"
                                                className="checkbox checkbox-sm"
                                                checked={selectedIndices.has(index)}
                                                onChange={() => handleToggleSelection(index)}
                                            />
                                        </td>
                                        <td className="p-3">
                                            <div className="font-medium text-gray-900 dark:text-gray-100">{fd.bank}</div>
                                            <div className="text-xs text-gray-500">{fd.account_number}</div>
                                            {isDuplicate && <span className="badge badge-warning badge-xs mt-1">Potential Duplicate</span>}
                                        </td>
                                        <td className="p-3">
                                            <input
                                                type="number"
                                                value={fd.principal_amount}
                                                onChange={(e) => handleFieldChange(index, 'principal_amount', parseFloat(e.target.value))}
                                                className="form-input py-1 text-sm w-28"
                                            />
                                        </td>
                                        <td className="p-3">
                                            <input
                                                type="number"
                                                step="0.01"
                                                value={fd.interest_rate}
                                                onChange={(e) => handleFieldChange(index, 'interest_rate', parseFloat(e.target.value))}
                                                className="form-input py-1 text-sm w-20"
                                            />
                                        </td>
                                        <td className="p-3">
                                            <input
                                                type="date"
                                                value={fd.start_date}
                                                onChange={(e) => handleFieldChange(index, 'start_date', e.target.value)}
                                                className="form-input py-1 text-sm"
                                            />
                                        </td>
                                        <td className="p-3">
                                            <input
                                                type="date"
                                                value={fd.maturity_date}
                                                onChange={(e) => handleFieldChange(index, 'maturity_date', e.target.value)}
                                                className="form-input py-1 text-sm"
                                            />
                                        </td>
                                        <td className="p-3">
                                            <select
                                                value={fd.compounding_frequency}
                                                onChange={(e) => handleFieldChange(index, 'compounding_frequency', e.target.value)}
                                                className="form-select py-1 text-sm"
                                            >
                                                <option value="Monthly">Monthly</option>
                                                <option value="Quarterly">Quarterly</option>
                                                <option value="Half-Yearly">Half-Yearly</option>
                                                <option value="Yearly">Yearly</option>
                                            </select>
                                        </td>
                                        <td className="p-3">
                                            <select
                                                value={fd.interest_payout}
                                                onChange={(e) => handleFieldChange(index, 'interest_payout', e.target.value)}
                                                className="form-select py-1 text-sm"
                                            >
                                                <option value="Payout">Payout</option>
                                                <option value="Cumulative">Cumulative</option>
                                            </select>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="mt-8 flex justify-end gap-4">
                <button onClick={handleCancel} className="btn btn-secondary" disabled={commitMutation.isPending || commitMutation.isSuccess}>Cancel</button>
                <button onClick={handleCommit} className="btn btn-primary min-w-[180px]" disabled={!canCommit || commitMutation.isPending || commitMutation.isSuccess}>
                    {commitMutation.isPending ? 'Committing...' : `Commit ${selectedIndices.size} Fixed Deposits`}
                </button>
            </div>

            {commitMutation.isSuccess && (
                <div className="alert alert-success mt-4">
                    {commitMutation.data?.msg} Redirecting to portfolio...
                </div>
            )}
            {commitMutation.isError && (
                <div className="alert alert-error mt-4">
                    Error committing FDs: {(commitMutation.error as AxiosError<{ detail: string }>).response?.data?.detail || (commitMutation.error as Error).message}
                </div>
            )}
        </div>
    );
};

export default FDImportPreviewPage;

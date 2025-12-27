import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortfolios } from '../../hooks/usePortfolios';
import { useCreateImportSession } from '../../hooks/useImport';
import { ArrowUpTrayIcon, LockClosedIcon } from '@heroicons/react/24/solid';
import { AxiosError } from 'axios';

const DataImportPage: React.FC = () => {
    const navigate = useNavigate();
    const [selectedPortfolio, setSelectedPortfolio] = useState<string>('');
    const [sourceType, setSourceType] = useState<string>('Generic CSV');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [password, setPassword] = useState('');
    const [passwordError, setPasswordError] = useState('');

    const { data: portfolios, isLoading: isLoadingPortfolios } = usePortfolios();
    const createImportSessionMutation = useCreateImportSession();

    useEffect(() => {
        if (createImportSessionMutation.isSuccess && createImportSessionMutation.data) {
            const sessionId = createImportSessionMutation.data.id;
            navigate(`/import/${sessionId}/preview`);
        }
    }, [createImportSessionMutation.isSuccess, createImportSessionMutation.data, navigate]);

    // Handle PASSWORD_REQUIRED error
    useEffect(() => {
        if (createImportSessionMutation.isError) {
            const error = createImportSessionMutation.error as AxiosError<{ detail: string }>;
            if (error.response?.status === 422 &&
                error.response?.data?.detail === 'PASSWORD_REQUIRED') {
                setShowPasswordModal(true);
                setPasswordError('');
            }
        }
    }, [createImportSessionMutation.isError, createImportSessionMutation.error]);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setSelectedFile(event.target.files[0]);
            // Reset password state when new file is selected
            setPassword('');
            setPasswordError('');
        }
    };

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!selectedPortfolio || !selectedFile || !sourceType) {
            alert('Please select a portfolio, a source type, and a file.');
            return;
        }
        createImportSessionMutation.mutate({
            portfolioId: selectedPortfolio,
            source_type: sourceType,
            file: selectedFile,
        });
    };

    const handlePasswordSubmit = () => {
        if (!password.trim()) {
            setPasswordError('Please enter the PDF password');
            return;
        }
        if (!selectedPortfolio || !selectedFile || !sourceType) {
            return;
        }
        setPasswordError('');
        createImportSessionMutation.mutate({
            portfolioId: selectedPortfolio,
            source_type: sourceType,
            file: selectedFile,
            password: password,
        });
    };

    const handlePasswordModalClose = () => {
        setShowPasswordModal(false);
        setPassword('');
        setPasswordError('');
        createImportSessionMutation.reset();
    };

    // Check if error is not PASSWORD_REQUIRED (to show normal error message)
    const isNonPasswordError = createImportSessionMutation.isError &&
        !((createImportSessionMutation.error as AxiosError<{ detail: string }>)
            .response?.data?.detail === 'PASSWORD_REQUIRED');

    return (
        <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-4">Import Transactions</h1>
            <p className="text-gray-600 dark:text-gray-400 mb-8">
                Upload your transaction history from a CSV file. Select the correct source type for accurate parsing.
            </p>

            <div className="card max-w-2xl mx-auto">
                <form onSubmit={handleSubmit}>
                    <div className="space-y-6">
                        {/* Portfolio Selector */}
                        <div className="form-group">
                            <label htmlFor="portfolio" className="form-label">
                                Select Portfolio
                            </label>
                            <select
                                id="portfolio"
                                value={selectedPortfolio}
                                onChange={(e) => setSelectedPortfolio(e.target.value)}
                                className="form-select"
                                disabled={isLoadingPortfolios || createImportSessionMutation.isPending}
                                required
                            >
                                <option value="" disabled>
                                    {isLoadingPortfolios ? 'Loading portfolios...' : 'Select a portfolio'}
                                </option>
                                {portfolios?.map((p) => (
                                    <option key={p.id} value={p.id}>
                                        {p.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Source Type Selector */}
                        <div className="form-group">
                            <label htmlFor="sourceType" className="form-label">
                                Statement Type
                            </label>
                            <select
                                id="sourceType"
                                value={sourceType}
                                onChange={(e) => setSourceType(e.target.value)}
                                className="form-select"
                                disabled={createImportSessionMutation.isPending}
                                required
                            >
                                <option value="Generic CSV">Generic CSV</option>
                                <option value="Zerodha Tradebook">Zerodha Tradebook</option>
                                <option value="ICICI Direct Tradebook">ICICI Direct Tradebook</option>
                                <option value="MFCentral CAS">MFCentral CAS (Mutual Funds)</option>
                                <option value="CAMS Statement">CAMS Statement (Mutual Funds)</option>
                                <option value="Zerodha Coin">Zerodha Coin (Mutual Funds)</option>
                                <option value="KFintech Statement">KFintech Statement PDF (Mutual Funds)</option>
                                <option value="KFintech XLS">KFintech Transaction XLS (Mutual Funds) - Recommended</option>
                            </select>
                        </div>

                        {/* File Upload */}
                        <div className="form-group">
                            <label htmlFor="file-upload" className="form-label">
                                Upload Statement
                            </label>
                            <div className="mt-2 flex justify-center rounded-lg border border-dashed border-gray-900/25 dark:border-gray-600 px-6 py-10">
                                <div className="text-center">
                                    <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-500" aria-hidden="true" />
                                    <div className="mt-4 flex text-sm leading-6 text-gray-600 dark:text-gray-400">
                                        <label
                                            htmlFor="file-upload"
                                            className="relative cursor-pointer rounded-md bg-white dark:bg-gray-800 font-semibold text-blue-600 dark:text-blue-400 focus-within:outline-none focus-within:ring-2 focus-within:ring-blue-600 focus-within:ring-offset-2 hover:text-blue-500"
                                        >
                                            <span>Upload a file</span>
                                            <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".csv,.xlsx,.xls,.pdf" />
                                        </label>
                                        <p className="pl-1">or drag and drop</p>
                                    </div>
                                    <p className="text-xs leading-5 text-gray-600 dark:text-gray-400">CSV, Excel, or PDF up to 10MB</p>
                                    {selectedFile && (
                                        <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mt-4">
                                            Selected: {selectedFile.name}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Submission and Status */}
                    <div className="mt-8">
                        <button type="submit" className="btn btn-primary w-full" disabled={!selectedPortfolio || !selectedFile || !sourceType || createImportSessionMutation.isPending}>
                            {createImportSessionMutation.isPending ? 'Uploading & Parsing...' : 'Upload and Preview'}
                        </button>

                        {isNonPasswordError && (
                            <div className="alert alert-error mt-4">
                                Error: {createImportSessionMutation.error.message}
                            </div>
                        )}
                    </div>
                </form>
            </div>

            {/* Password Modal */}
            {showPasswordModal && (
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
                        <div className="flex items-center mb-4">
                            <LockClosedIcon className="h-6 w-6 text-blue-600 mr-2" />
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                Password Required
                            </h3>
                        </div>
                        <p className="text-gray-600 dark:text-gray-400 mb-4">
                            This PDF is password-protected. Please enter the password to continue.
                        </p>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter PDF password"
                            className="form-input w-full mb-2"
                            autoFocus
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    handlePasswordSubmit();
                                }
                            }}
                        />
                        {passwordError && (
                            <p className="text-red-500 text-sm mb-2">{passwordError}</p>
                        )}
                        <div className="flex justify-end gap-3 mt-4">
                            <button
                                type="button"
                                onClick={handlePasswordModalClose}
                                className="btn btn-secondary"
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                onClick={handlePasswordSubmit}
                                className="btn btn-primary"
                                disabled={createImportSessionMutation.isPending}
                            >
                                {createImportSessionMutation.isPending ? 'Processing...' : 'Submit'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DataImportPage;
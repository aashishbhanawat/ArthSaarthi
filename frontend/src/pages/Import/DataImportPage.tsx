import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortfolios } from '../../hooks/usePortfolios';
import { useCreateImportSession } from '../../hooks/useImport';
import { ArrowUpTrayIcon } from '@heroicons/react/24/solid';

const DataImportPage: React.FC = () => {
    const navigate = useNavigate();
    const [selectedPortfolio, setSelectedPortfolio] = useState<string>('');
    const [sourceType, setSourceType] = useState<string>('Generic CSV');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const { data: portfolios, isLoading: isLoadingPortfolios } = usePortfolios();
    const createImportSessionMutation = useCreateImportSession();

    useEffect(() => {
        if (createImportSessionMutation.isSuccess && createImportSessionMutation.data) {
            const sessionId = createImportSessionMutation.data.id;
            navigate(`/import/${sessionId}/preview`);
        }
    }, [createImportSessionMutation.isSuccess, createImportSessionMutation.data, navigate]);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setSelectedFile(event.target.files[0]);
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

    return (
        <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-4">Import Transactions</h1>
            <p className="text-gray-600 mb-8">
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
                            </select>
                        </div>

                        {/* File Upload */}
                        <div className="form-group">
                            <label htmlFor="file-upload" className="form-label">
                                Upload Statement
                            </label>
                            <div className="mt-2 flex justify-center rounded-lg border border-dashed border-gray-900/25 px-6 py-10">
                                <div className="text-center">
                                    <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-gray-300" aria-hidden="true" />
                                    <div className="mt-4 flex text-sm leading-6 text-gray-600">
                                        <label
                                            htmlFor="file-upload"
                                            className="relative cursor-pointer rounded-md bg-white font-semibold text-blue-600 focus-within:outline-none focus-within:ring-2 focus-within:ring-blue-600 focus-within:ring-offset-2 hover:text-blue-500"
                                        >
                                            <span>Upload a file</span>
                                            <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".csv" />
                                        </label>
                                        <p className="pl-1">or drag and drop</p>
                                    </div>
                                    <p className="text-xs leading-5 text-gray-600">CSV up to 10MB</p>
                                    {selectedFile && (
                                        <p className="text-sm font-medium text-gray-800 mt-4">
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

                        {createImportSessionMutation.isError && (
                            <div className="alert alert-error mt-4">
                                Error: {createImportSessionMutation.error.message}
                            </div>
                        )}
                    </div>
                </form>
            </div>
        </div>
    );
};

export default DataImportPage;
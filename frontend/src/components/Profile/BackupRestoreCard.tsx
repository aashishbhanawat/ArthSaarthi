import React, { useState, useRef } from 'react';
import { isAxiosError } from 'axios';
import { ArrowDownTrayIcon, ArrowUpTrayIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { downloadBackup, restoreBackup } from '../../services/userApi';
import { useToast } from '../../context/ToastContext';

const BackupRestoreCard: React.FC = () => {
    const [isRestoreModalOpen, setIsRestoreModalOpen] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [confirmationWord, setConfirmationWord] = useState('');
    const [loading, setLoading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { showToast } = useToast();

    const handleDownload = async () => {
        try {
            setLoading(true);
            await downloadBackup();
            showToast('Backup downloaded successfully', 'success');
        } catch (error) {
            showToast('Failed to download backup', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleRestoreClick = () => {
        if (!file) {
            showToast('Please select a backup file first', 'error');
            return;
        }
        setIsRestoreModalOpen(true);
    };

    const confirmRestore = async () => {
        if (!file) return;
        if (confirmationWord.toUpperCase() !== 'DELETE') return;

        try {
            setLoading(true);
            await restoreBackup(file);
            showToast('Data restored successfully. Please refresh the page.', 'success');
            setIsRestoreModalOpen(false);
            setFile(null);
            setConfirmationWord('');
            if (fileInputRef.current) fileInputRef.current.value = '';
        } catch (error: unknown) {
            let message = 'Unknown error';
            if (isAxiosError(error) && error.response?.data?.detail) {
                message = error.response.data.detail;
            } else if (error instanceof Error) {
                message = error.message;
            }
            showToast(`Restore failed: ${message}`, 'error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Backup & Restore</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Backup Section */}
                <div className="border rounded-lg p-4 flex flex-col items-start">
                    <h3 className="font-medium mb-2">Export Data</h3>
                    <p className="text-sm text-gray-600 mb-4">
                        Download a copy of your data including portfolios, transactions, and settings.
                    </p>
                    <button
                        onClick={handleDownload}
                        disabled={loading}
                        className="mt-auto btn btn-primary flex items-center"
                    >
                        <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                        Download Backup
                    </button>
                </div>

                {/* Restore Section */}
                <div className="border rounded-lg p-4 flex flex-col items-start">
                    <h3 className="font-medium mb-2">Import Data</h3>
                    <p className="text-sm text-gray-600 mb-4">
                        Restore your data from a backup file.
                    </p>
                    <input
                        type="file"
                        accept=".json"
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 mb-4"
                    />
                    <button
                        onClick={handleRestoreClick}
                        disabled={loading || !file}
                        className="mt-auto btn btn-danger flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <ArrowUpTrayIcon className="h-5 w-5 mr-2" />
                        Restore from Backup
                    </button>
                </div>
            </div>

            {/* Confirmation Modal */}
            {isRestoreModalOpen && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
                    <div className="relative p-5 border w-96 shadow-lg rounded-md bg-white">
                        <div className="mt-3 text-center">
                            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                                <ExclamationTriangleIcon className="h-6 w-6 text-red-600" />
                            </div>
                            <h3 className="text-lg leading-6 font-medium text-gray-900 mt-4">Warning: Data Loss</h3>
                            <div className="mt-2 px-7 py-3">
                                <p className="text-sm text-gray-500">
                                    Restoring a backup will <strong>permanently delete</strong> all your current data. This action cannot be undone.
                                </p>
                                <p className="text-sm text-gray-500 mt-2">
                                    Type <strong>DELETE</strong> to confirm.
                                </p>
                                <input
                                    type="text"
                                    className="mt-3 w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                                    placeholder="DELETE"
                                    value={confirmationWord}
                                    onChange={(e) => setConfirmationWord(e.target.value)}
                                />
                            </div>
                            <div className="items-center px-4 py-3">
                                <button
                                    id="confirm-restore-btn"
                                    className="px-4 py-2 bg-red-600 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
                                    onClick={confirmRestore}
                                    disabled={confirmationWord.toUpperCase() !== 'DELETE' || loading}
                                >
                                    {loading ? 'Restoring...' : 'Confirm Restore'}
                                </button>
                                <button
                                    className="px-4 py-2 bg-gray-100 text-black text-base font-medium rounded-md w-full shadow-sm hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-300 mt-2"
                                    onClick={() => { setIsRestoreModalOpen(false); setConfirmationWord(''); }}
                                    disabled={loading}
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default BackupRestoreCard;

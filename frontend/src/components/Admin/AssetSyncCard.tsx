import React, { useState } from 'react';
import { syncAssets, AssetSyncResponse } from '../../services/adminApi';
import { toast } from 'react-hot-toast';
import axios from 'axios';

/**
 * AssetSyncCard - Admin component for triggering manual asset master sync.
 * FR2.3: Manual Asset Seeding
 */
const AssetSyncCard: React.FC = () => {
    const [isLoading, setIsLoading] = useState(false);

    const handleSync = async () => {
        setIsLoading(true);

        try {
            const response: AssetSyncResponse = await syncAssets();

            if (response.status === 'success') {
                const { newly_added, updated, total_processed } = response.data;
                toast.success(
                    `Asset sync complete: ${newly_added} new, ${updated} updated (${total_processed} total)`,
                    { duration: 5000 }
                );
            }
        } catch (error) {
            if (axios.isAxiosError(error)) {
                if (error.response?.status === 429) {
                    const retryAfter = error.response.headers['retry-after'];
                    toast.error(
                        `Rate limit exceeded. Please wait ${retryAfter || '5 minutes'} before trying again.`,
                        { duration: 5000 }
                    );
                } else if (error.response?.status === 403) {
                    toast.error('You do not have permission to perform this action.');
                } else if (error.code === 'ECONNABORTED') {
                    toast.error('Request timed out. The sync may still be in progress.');
                } else {
                    toast.error(
                        error.response?.data?.detail || 'Failed to sync assets. Please try again.'
                    );
                }
            } else {
                toast.error('An unexpected error occurred.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="card">
            <div className="card-header">
                <h3 className="card-title">System Maintenance</h3>
            </div>
            <div className="card-body">
                <div className="mb-4">
                    <h4 className="text-lg font-medium mb-2">Asset Master Sync</h4>
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                        Download and update the latest stock, mutual fund, and bond data from
                        exchanges (NSDL, BSE, NSE). This process may take a few minutes.
                    </p>
                    <button
                        onClick={handleSync}
                        disabled={isLoading}
                        className="btn btn-primary flex items-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <svg
                                    className="animate-spin h-5 w-5"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                >
                                    <circle
                                        className="opacity-25"
                                        cx="12"
                                        cy="12"
                                        r="10"
                                        stroke="currentColor"
                                        strokeWidth="4"
                                    />
                                    <path
                                        className="opacity-75"
                                        fill="currentColor"
                                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                    />
                                </svg>
                                Syncing Assets...
                            </>
                        ) : (
                            <>
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    strokeWidth={1.5}
                                    stroke="currentColor"
                                    className="w-5 h-5"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
                                    />
                                </svg>
                                Sync Assets
                            </>
                        )}
                    </button>
                </div>
                <p className="text-xs text-gray-500">
                    Note: Rate limited to once every 5 minutes.
                </p>
            </div>
        </div>
    );
};

export default AssetSyncCard;

import React, { useState } from 'react';
import { isAxiosError } from 'axios';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import { syncAssets, AssetSyncResponse } from '../../services/adminApi';
import { useToast } from '../../context/ToastContext';

/**
 * AssetSyncCard - Admin component for triggering manual asset master sync.
 * FR2.3: Manual Asset Seeding
 */
const AssetSyncCard: React.FC = () => {
    const [isLoading, setIsLoading] = useState(false);
    const { showToast } = useToast();

    const handleSync = async () => {
        setIsLoading(true);

        try {
            const response: AssetSyncResponse = await syncAssets();

            if (response.status === 'success') {
                const { newly_added, updated, total_processed } = response.data;
                showToast(
                    `Asset sync complete: ${newly_added} new, ${updated} updated (${total_processed} total)`,
                    'success'
                );
            }
        } catch (error: unknown) {
            if (isAxiosError(error)) {
                if (error.response?.status === 429) {
                    const retryAfter = error.response.headers['retry-after'];
                    showToast(
                        `Rate limit exceeded. Please wait ${retryAfter || '5 minutes'} before trying again.`,
                        'error'
                    );
                } else if (error.response?.status === 403) {
                    showToast('You do not have permission to perform this action.', 'error');
                } else if (error.code === 'ECONNABORTED') {
                    showToast('Request timed out. The sync may still be in progress.', 'error');
                } else {
                    const message = error.response?.data?.detail || 'Failed to sync assets. Please try again.';
                    showToast(message, 'error');
                }
            } else {
                showToast('An unexpected error occurred.', 'error');
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">System Maintenance</h2>
            <div className="border rounded-lg p-4">
                <h3 className="font-medium mb-2">Asset Master Sync</h3>
                <p className="text-sm text-gray-600 mb-4">
                    Download and update the latest stock, mutual fund, and bond data from
                    exchanges (NSDL, BSE, NSE). This process may take a few minutes.
                </p>
                <button
                    onClick={handleSync}
                    disabled={isLoading}
                    className="btn btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <ArrowPathIcon className={`h-5 w-5 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                    {isLoading ? 'Syncing Assets...' : 'Sync Assets'}
                </button>
                <p className="text-xs text-gray-500 mt-3">
                    Note: Rate limited to once every 5 minutes.
                </p>
            </div>
        </div>
    );
};

export default AssetSyncCard;

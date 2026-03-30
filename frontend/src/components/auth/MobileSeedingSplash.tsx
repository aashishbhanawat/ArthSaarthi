import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import { ArrowPathIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface SeedingStatusResponse {
    status: 'idle' | 'in_progress' | 'complete' | 'failed' | 'needs_seeding';
    progress: number;
    message: string;
    asset_count: number;
    error?: string;
}

interface MobileSeedingSplashProps {
    onComplete: () => void;
}

const MobileSeedingSplash: React.FC<MobileSeedingSplashProps> = ({ onComplete }) => {
    const [statusResponse, setStatusResponse] = useState<SeedingStatusResponse | null>(null);
    const [isRetrying, setIsRetrying] = useState(false);

    const fetchStatus = useCallback(async () => {
        try {
            const response = await api.get<SeedingStatusResponse>('/api/v1/system/seeding-status');
            setStatusResponse(response.data);

            if (response.data.status === 'complete' || (response.data.status === 'idle' && response.data.asset_count > 10000)) {
                onComplete();
            }
        } catch (error) {
            console.error("Failed to fetch seeding status", error);
        }
    }, [onComplete]);

    useEffect(() => {
        // Initial fetch
        fetchStatus();

        // Poll every 2 seconds
        const interval = setInterval(fetchStatus, 2000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    const handleRetry = async () => {
        setIsRetrying(true);
        try {
            await api.post('/api/v1/system/seeding-reset');
            await api.post('/api/v1/system/trigger-seeding');
            fetchStatus();
        } catch (error) {
            console.error("Failed to retry seeding", error);
        } finally {
            setIsRetrying(false);
        }
    };

    if (!statusResponse) {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-center space-y-4">
                <ArrowPathIcon className="h-12 w-12 text-blue-500 animate-spin mx-auto" />
                <h2 className="text-xl font-semibold">Connecting to Engine...</h2>
                <p className="text-gray-500 dark:text-gray-400">Please wait while ArthSaarthi initializes.</p>
            </div>
        );
    }

    if (statusResponse.status === 'failed') {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-center space-y-4">
                <ExclamationTriangleIcon className="h-16 w-16 text-red-500 mx-auto" />
                <h2 className="text-xl font-bold text-red-600 dark:text-red-400">Initialization Failed</h2>
                <p className="text-gray-700 dark:text-gray-300">{statusResponse.error || 'Failed to seed master data.'}</p>
                <button
                    onClick={handleRetry}
                    disabled={isRetrying}
                    className="btn btn-primary mt-4"
                >
                    {isRetrying ? 'Retrying...' : 'Retry Initialization'}
                </button>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center p-8 text-center space-y-6">
            <div className="relative w-24 h-24">
                <svg className="animate-spin w-full h-full text-blue-200 dark:text-blue-900" viewBox="0 0 100 100">
                    <circle className="opacity-25" cx="50" cy="50" r="45" stroke="currentColor" strokeWidth="10" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M50 5a45 45 0 0 1 45 45h-10a35 35 0 0 0-35-35V5z" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center text-lg font-bold text-blue-600 dark:text-blue-400">
                    {statusResponse.progress}%
                </div>
            </div>

            <div>
                <h2 className="text-xl font-bold mb-2">Preparing Asset Database</h2>
                <div className="flex flex-col space-y-1">
                    <p className="text-blue-600 dark:text-blue-400 font-medium text-sm">
                        {statusResponse.message || 'Loading synchronized assets...'}
                    </p>
                    <p className="text-gray-500 dark:text-gray-400 text-xs">
                        Total Assets: <span className="font-mono">{statusResponse.asset_count.toLocaleString()}</span>
                    </p>
                </div>
            </div>

            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
                <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${statusResponse.progress}%` }}
                ></div>
            </div>

            <p className="text-xs text-gray-400 dark:text-gray-500 mt-4">
                This is a one-time process and may take 10-20 minutes depending on your network.
            </p>
        </div>
    );
};

export default MobileSeedingSplash;

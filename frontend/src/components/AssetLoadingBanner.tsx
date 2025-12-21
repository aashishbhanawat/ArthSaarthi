import { useQuery } from '@tanstack/react-query';
import apiClient from '../services/api';

interface InitStatus {
    setup_needed: boolean;
    assets_ready: boolean;
    asset_count: number;
}

const fetchInitStatus = async (): Promise<InitStatus> => {
    const response = await apiClient.get('/api/v1/auth/init-status');
    return response.data;
};

/**
 * Banner that shows during first-time asset seeding.
 * Only shows if assets_ready is false (count < 1000).
 * Polls every 5 seconds until assets are ready.
 */
const AssetLoadingBanner = () => {
    const { data, isLoading } = useQuery({
        queryKey: ['init-status'],
        queryFn: fetchInitStatus,
        refetchInterval: (data) => {
            // Stop polling once assets are ready
            if (data?.state?.data?.assets_ready) {
                return false;
            }
            return 5000; // Poll every 5 seconds
        },
    });

    // Don't show anything while loading or if assets are ready
    if (isLoading || !data || data.assets_ready) {
        return null;
    }

    return (
        <div className="bg-blue-500 text-white px-4 py-2 text-center text-sm">
            <span className="inline-flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Loading asset database... ({data.asset_count.toLocaleString()} assets loaded)
            </span>
        </div>
    );
};

export default AssetLoadingBanner;

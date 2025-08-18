import React from 'react';
import { PortfolioAnalytics } from '../../types/analytics';

interface AnalyticsCardProps {
    analytics: PortfolioAnalytics | undefined;
    isLoading: boolean;
    error: Error | null;
}

const AnalyticsCard: React.FC<AnalyticsCardProps> = ({ analytics, isLoading, error }) => {
    if (isLoading) {
        return <div className="card">Loading analytics...</div>;
    }

    if (error) {
        return <div className="card">Error: {error.message}</div>;
    }

    if (!analytics) {
        return <div className="card">No analytics data available.</div>;
    }

    return (
        <div className="card">
            <h3 className="text-lg font-semibold mb-2">Advanced Analytics</h3>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <p className="text-sm text-gray-500">Realized XIRR</p>
                    <p className="text-xl font-bold">{analytics.realized_xirr != null ? `${(analytics.realized_xirr * 100).toFixed(2)}%` : 'N/A'}</p>
                </div>
                <div>
                    <p className="text-sm text-gray-500">Sharpe Ratio</p>
                    <p className="text-xl font-bold">{analytics.sharpe_ratio != null ? analytics.sharpe_ratio.toFixed(2) : 'N/A'}</p>
                </div>
            </div>
        </div>
    );
};

export default AnalyticsCard;

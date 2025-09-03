import React from 'react';
import { PortfolioSummary as PortfolioSummaryType } from '../../types/holding';
import { usePrivacySensitiveCurrency } from '../../utils/formatting';

interface SummaryItemProps {
    label: string;
    value: number;
    isPnl?: boolean; // To apply color coding for Profit/Loss
}

const SummaryItem: React.FC<SummaryItemProps> = ({ label, value, isPnl = false }) => {
    const formatCurrency = usePrivacySensitiveCurrency();
    const getPnlColor = (pnl: number) => {
        if (pnl > 0) return 'text-green-600';
        if (pnl < 0) return 'text-red-600';
        return 'text-gray-900';
    };

    const valueColor = isPnl ? getPnlColor(value) : 'text-gray-900';

    return (
        <div className="bg-gray-50 p-4 rounded-lg shadow-sm text-center">
            <p className="text-sm text-gray-500 truncate">{label}</p>
            <p className={`text-2xl font-bold ${valueColor}`}>{formatCurrency(value)}</p>
        </div>
    );
};


interface PortfolioSummaryProps {
    summary: PortfolioSummaryType | undefined;
    isLoading: boolean;
    error: Error | null;
}

const PortfolioSummary: React.FC<PortfolioSummaryProps> = ({ summary, isLoading, error }) => {
    if (isLoading) {
        return (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
                {Array.from({ length: 5 }).map((_, index) => (
                     <div key={index} className="bg-gray-50 p-4 rounded-lg shadow-sm animate-pulse">
                        <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto mb-2"></div>
                        <div className="h-8 bg-gray-200 rounded w-1/2 mx-auto"></div>
                    </div>
                ))}
            </div>
        );
    }

    if (error || !summary) return null;

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
            <SummaryItem label="Total Value" value={summary.total_value} />
            <SummaryItem label="Day's P&L" value={summary.days_pnl} isPnl />
            <SummaryItem label="Unrealized P&L" value={summary.total_unrealized_pnl} isPnl />
            <SummaryItem label="Realized P&L" value={summary.total_realized_pnl} isPnl />
            <SummaryItem label="Total Invested" value={summary.total_invested_amount} />
        </div>
    );
};

export default PortfolioSummary;

import React from "react";
import { useDashboardSummary } from '../hooks/useDashboard';
import SummaryCard from '../components/Dashboard/SummaryCard';
import TopMoversTable from '../components/Dashboard/TopMoversTable';

const DashboardPage: React.FC = () => {
    const { data: summary, isLoading, isError, error } = useDashboardSummary();

    if (isLoading) {
        return <div className="text-center p-8">Loading dashboard data...</div>;
    }

    if (isError) {
        return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;
    }

    const formatCurrency = (value: string) => {
        const number = parseFloat(value);
        const formatted = Math.abs(number).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
        return number < 0 ? `-$${formatted}` : `$${formatted}`;
    };

    const getPnlColor = (value: string) => {
        const number = parseFloat(value);
        if (number > 0) return 'text-green-600';
        if (number < 0) return 'text-red-600';
        return 'text-gray-800';
    };

    return (
        <div>
            <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <SummaryCard
                    title="Total Value"
                    value={formatCurrency(summary?.total_value || '0')}
                />
                <SummaryCard
                    title="Unrealized P/L"
                    value={formatCurrency(summary?.total_unrealized_pnl || '0')}
                    valueColorClass={getPnlColor(summary?.total_unrealized_pnl || '0')}
                />
                <SummaryCard
                    title="Realized P/L"
                    value={formatCurrency(summary?.total_realized_pnl || '0')}
                    valueColorClass={getPnlColor(summary?.total_realized_pnl || '0')}
                />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <TopMoversTable assets={summary?.top_movers || []} />
                {/* Placeholder for a chart */}
                <div className="card"><h3 className="text-xl font-semibold mb-4">Portfolio History</h3><div className="flex items-center justify-center h-48 bg-gray-100 rounded-md text-gray-400"><p>Chart will be rendered here.</p></div></div>
            </div>
        </div>
    );    
};

export default DashboardPage;
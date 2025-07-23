import React from 'react';
import { useDashboardSummary } from '../hooks/useDashboard';
import SummaryCard from '../components/Dashboard/SummaryCard';
import TopMoversTable from '../components/Dashboard/TopMoversTable';
import PortfolioHistoryChart from '../components/Dashboard/PortfolioHistoryChart';
import AssetAllocationChart from '../components/Dashboard/AssetAllocationChart';

const DashboardPage: React.FC = () => {
  const { data: summary, isLoading, isError, error } = useDashboardSummary();

  if (isLoading) {
    return <div className="text-center p-8">Loading dashboard data...</div>;
  }

  if (isError) {
    return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;
  }

  const formatCurrency = (value: number | string) => {
    const number = Number(value);
    const formatted = Math.abs(number).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return number < 0 ? `-$${formatted}` : `$${formatted}`;
  };

  const getPnlColor = (value: number | string) => {
    const number = Number(value);
    if (number > 0) return 'text-green-600';
    if (number < 0) return 'text-red-600';
    return 'text-gray-800';
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SummaryCard
          title="Total Value"
          value={formatCurrency(summary?.total_value || 0)}
        />
        <SummaryCard
          title="Unrealized P/L"
          value={formatCurrency(summary?.total_unrealized_pnl || 0)}
          valueColorClass={getPnlColor(summary?.total_unrealized_pnl || 0)}
        />
        <SummaryCard
          title="Realized P/L"
          value={formatCurrency(summary?.total_realized_pnl || 0)}
          valueColorClass={getPnlColor(summary?.total_realized_pnl || 0)}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <PortfolioHistoryChart />
        <AssetAllocationChart />
      </div>

      <TopMoversTable assets={summary?.top_movers || []} />
    </div>
  );
};

export default DashboardPage;
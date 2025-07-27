import React from 'react';
import { useDashboardSummary } from '../hooks/useDashboard';
import SummaryCard from '../components/Dashboard/SummaryCard';
import TopMoversTable from '../components/Dashboard/TopMoversTable';
import PortfolioHistoryChart from '../components/Dashboard/PortfolioHistoryChart';
import AssetAllocationChart from '../components/Dashboard/AssetAllocationChart';
import { formatCurrency } from '../utils/formatting';

const DashboardPage: React.FC = () => {
  const { data: summary, isLoading, isError, error } = useDashboardSummary();

  if (isLoading) {
    return <div className="text-center p-8">Loading dashboard data...</div>;
  }

  if (isError) {
    return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SummaryCard title="Total Value" value={Number(summary?.total_value || 0)} />
        <SummaryCard title="Unrealized P/L" value={Number(summary?.total_unrealized_pnl || 0)} isPnl={true} />
        <SummaryCard title="Realized P/L" value={Number(summary?.total_realized_pnl || 0)} isPnl={true} />
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
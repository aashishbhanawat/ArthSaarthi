import { useDashboardSummary } from '../hooks/useDashboard';
import SummaryCard from '../components/Dashboard/SummaryCard';
import TopMoversTable from '../components/Dashboard/TopMoversTable';
import PortfolioHistoryChart from '../components/Dashboard/PortfolioHistoryChart';
import AssetAllocationChart from '../components/Dashboard/AssetAllocationChart';
import HelpLink from '../components/HelpLink';


const DashboardPage = () => {
  const { data: summary, isLoading, isError, error } = useDashboardSummary();

  if (isLoading) {
    return <div className="text-center p-8">Loading dashboard data...</div>;
  }

  if (isError) {
    return <div className="text-center p-8 text-red-500">Error loading dashboard data.</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <HelpLink sectionId="dashboard" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SummaryCard title="Total Value" value={Number(summary?.total_value || 0)} />
        <SummaryCard title="Unrealized P/L" value={Number(summary?.total_unrealized_pnl || 0)} isPnl={true} />
        <SummaryCard title="Realized P/L" value={Number(summary?.total_realized_pnl || 0)} isPnl={true} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <h2 className="text-xl font-semibold">Portfolio History</h2>
            <HelpLink sectionId="dashboard-portfolio-history" />
          </div>
          <PortfolioHistoryChart />
        </div>
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <h2 className="text-xl font-semibold">Asset Allocation</h2>
            <HelpLink sectionId="dashboard-asset-allocation" />
          </div>
          <AssetAllocationChart />
        </div>
      </div>

      <div className="card p-6">
        <div className="flex items-center mb-4">
          <h2 className="text-xl font-semibold">Top Movers</h2>
          <HelpLink sectionId="dashboard-top-movers" />
        </div>
        <TopMoversTable assets={summary?.top_movers || []} />
      </div>
    </div>
  );
};

export default DashboardPage;
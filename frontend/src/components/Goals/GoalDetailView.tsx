import React, { useState, useMemo } from 'react';
import { useGoal, useCreateGoalLink, useDeleteGoalLink } from '../../hooks/useGoals';
import AssetLinkModal from '../modals/AssetLinkModal';
import { usePrivacySensitiveCurrency, formatDate } from '../../utils/formatting';
import { TrashIcon, LinkIcon } from '@heroicons/react/24/outline';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface GoalDetailViewProps {
  goalId: string;
}

const SummaryItem: React.FC<{ label: string; value: React.ReactNode; }> = ({ label, value }) => (
  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg shadow-sm">
    <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{label}</p>
    <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1 truncate">{value}</div>
  </div>
);

const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => (
  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
    <div
      className="bg-indigo-600 h-4 rounded-full transition-all duration-500"
      style={{ width: `${Math.min(progress, 100)}%` }}
    ></div>
  </div>
);


const GoalDetailView: React.FC<GoalDetailViewProps> = ({ goalId }) => {
  const { data: goal, isLoading, error } = useGoal(goalId);
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);
  const createGoalLink = useCreateGoalLink();
  const deleteGoalLink = useDeleteGoalLink();
  const formatCurrency = usePrivacySensitiveCurrency();

  const handleLink = (linkData: { portfolio_id?: string; asset_id?: string }) => {
    createGoalLink.mutate({ goalId, link: { ...linkData, goal_id: goalId } });
  };

  const handleUnlink = (linkId: string) => {
    if (window.confirm('Are you sure you want to unlink this item?')) {
      deleteGoalLink.mutate({ goalId, linkId });
    }
  };

  const chartData = useMemo(() => {
    if (!goal || !goal.projection_chart_data) return { labels: [], datasets: [] };
    return {
      labels: goal.projection_chart_data.map((point) => formatDate(point.date)) || [],
      datasets: [
        {
          label: 'Projected Value (Current holdings)',
          data: goal.projection_chart_data.map((point) => point.projected_value) || [],
          borderColor: 'rgb(59, 130, 246)', // blue-500
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: false,
          tension: 0.15,
          pointRadius: 2,
        },
        {
          label: 'Target Path (with required SIP)',
          data: goal.projection_chart_data.map((point) => point.target_value) || [],
          borderColor: 'rgb(16, 185, 129)', // emerald-500
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderDash: [5, 5],
          fill: false,
          tension: 0.15,
          pointRadius: 2,
        }
      ]
    };
  }, [goal]);

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: 'rgba(156, 163, 175, 1)',
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: { dataset: { label?: string }; parsed: { y: number | null } }) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += formatCurrency(context.parsed.y);
            }
            return label;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(156, 163, 175, 0.05)',
        },
        ticks: {
          color: 'rgba(156, 163, 175, 1)',
        }
      },
      y: {
        grid: {
          color: 'rgba(156, 163, 175, 0.05)',
        },
        ticks: {
          color: 'rgba(156, 163, 175, 1)',
          callback: function(value: string | number) {
            const numericValue = typeof value === 'number' ? value : parseFloat(value);
            return formatCurrency(numericValue);
          }
        }
      }
    }
  }), [formatCurrency]);

  if (isLoading) return <div className="dark:text-gray-300">Loading goal details...</div>;
  if (error) return <div className="dark:text-gray-300">An error occurred: {(error as Error).message}</div>;
  if (!goal) return <div className="dark:text-gray-300">Goal not found.</div>;

  return (
    <div className="space-y-8">
      {/* Summary Card */}
      <div className="card">
        <div className="card-body">
          <h2 className="card-title dark:text-gray-100">Summary</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
            <SummaryItem label="Target Amount" value={formatCurrency(goal.target_amount)} />
            <SummaryItem label="Current Amount" value={formatCurrency(goal.current_amount)} />
            <SummaryItem label="Target Date" value={formatDate(goal.target_date)} />
            <SummaryItem label="Projected Future Value" value={goal.projected_future_value !== undefined ? formatCurrency(goal.projected_future_value) : 'N/A'} />
            <SummaryItem
              label="Required Monthly SIP"
              value={goal.required_sip !== undefined ? `${formatCurrency(goal.required_sip)} / mo` : 'N/A'}
            />
            <SummaryItem label="Calculated Return Rate" value={`${(goal.calculated_return_rate ?? goal.expected_return ?? 10).toFixed(2)}%`} />
            <SummaryItem label="Linked Assets XIRR" value={goal.linked_assets_xirr !== undefined && goal.linked_assets_xirr !== 0 ? `${goal.linked_assets_xirr.toFixed(2)}%` : 'N/A'} />
            <SummaryItem 
              label="Goal Status" 
              value={
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-semibold leading-5 ${
                  goal.status === 'On Track' 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' 
                    : 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
                }`}>
                  {goal.status ?? 'Off Track'}
                </span>
              } 
            />
          </div>
        </div>
      </div>

      {/* Progress Card */}
      <div className="card">
        <div className="card-body">
          <h2 className="card-title dark:text-gray-100">Progress</h2>
          <div className="mt-4">
            <ProgressBar progress={goal.progress} />
            <p className="text-right font-semibold text-gray-700 dark:text-gray-300 mt-2">{goal.progress.toFixed(2)}%</p>
          </div>
        </div>
      </div>

      {/* Projection Chart Card */}
      {goal.projection_chart_data && goal.projection_chart_data.length > 0 && (
        <div className="card">
          <div className="card-body">
            <h2 className="card-title dark:text-gray-100 mb-4">Growth Projection Path</h2>
            <div className="h-80 w-full relative">
              <Line options={chartOptions} data={chartData} />
            </div>
          </div>
        </div>
      )}

      {/* Linked Items Card */}
      <div className="card">
        <div className="card-body">
          <div className="flex justify-between items-center">
            <h2 className="card-title dark:text-gray-100">Linked Items</h2>
            <button onClick={() => setIsLinkModalOpen(true)} className="btn btn-secondary btn-sm">
              <LinkIcon className="h-5 w-5 mr-2" aria-hidden="true" />
              Link Item
            </button>
          </div>
          <div className="mt-4 space-y-3">
            {goal.links.length > 0 ? goal.links.map(link => (
              <div key={link.id} className="flex justify-between items-center bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                <div>
                  <p className="font-semibold dark:text-gray-100">{link.asset?.name || link.portfolio?.name}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{link.asset ? `Asset: ${link.asset.ticker_symbol}` : 'Portfolio'}</p>
                </div>
                <button
                  onClick={() => handleUnlink(link.id)}
                  className="btn btn-ghost btn-sm text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30"
                  disabled={deleteGoalLink.isPending}
                >
                  <TrashIcon className="h-5 w-5" aria-hidden="true" />
                </button>
              </div>
            )) : (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">No items linked to this goal yet.</p>
            )}
          </div>
        </div>
      </div>

      <AssetLinkModal
        isOpen={isLinkModalOpen}
        onClose={() => setIsLinkModalOpen(false)}
        onLink={handleLink}
        goal={goal}
      />
    </div>
  );
};

export default GoalDetailView;

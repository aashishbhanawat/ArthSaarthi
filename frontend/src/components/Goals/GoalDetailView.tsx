import React, { useState } from 'react';
import { useGoal, useCreateGoalLink, useDeleteGoalLink } from '../../hooks/useGoals';
import AssetLinkModal from '../modals/AssetLinkModal';
import { formatCurrency, formatDate } from '../../utils/formatting';
import { TrashIcon, LinkIcon } from '@heroicons/react/24/outline';

interface GoalDetailViewProps {
  goalId: string;
}

const SummaryItem: React.FC<{ label: string; value: string | number; }> = ({ label, value }) => (
    <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
        <p className="text-sm text-gray-500 truncate">{label}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
);

const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => (
    <div className="w-full bg-gray-200 rounded-full h-4">
        <div
            className="bg-indigo-600 h-4 rounded-full"
            style={{ width: `${Math.min(progress, 100)}%` }}
        ></div>
    </div>
);


const GoalDetailView: React.FC<GoalDetailViewProps> = ({ goalId }) => {
  const { data: goal, isLoading, error } = useGoal(goalId);
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);
  const createGoalLink = useCreateGoalLink();
  const deleteGoalLink = useDeleteGoalLink();

  const handleLink = (linkData: { portfolio_id?: string; asset_id?: string }) => {
    createGoalLink.mutate({ goalId, link: { ...linkData, goal_id: goalId } });
  };

  const handleUnlink = (linkId: string) => {
    if (window.confirm('Are you sure you want to unlink this item?')) {
        deleteGoalLink.mutate({ goalId, linkId });
    }
  };

  if (isLoading) return <div>Loading goal details...</div>;
  if (error) return <div>An error occurred: {(error as Error).message}</div>;
  if (!goal) return <div>Goal not found.</div>;

  return (
    <div className="space-y-8">
      {/* Summary Card */}
      <div className="card">
        <div className="card-body">
            <h2 className="card-title">Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <SummaryItem label="Target Amount" value={formatCurrency(goal.target_amount)} />
                <SummaryItem label="Current Amount" value={formatCurrency(goal.current_amount)} />
                <SummaryItem label="Target Date" value={formatDate(goal.target_date)} />
            </div>
        </div>
      </div>

      {/* Progress Card */}
      <div className="card">
        <div className="card-body">
            <h2 className="card-title">Progress</h2>
            <div className="mt-4">
                <ProgressBar progress={goal.progress} />
                <p className="text-right font-semibold text-gray-700 mt-2">{goal.progress.toFixed(2)}%</p>
            </div>
        </div>
      </div>

      {/* Linked Items Card */}
      <div className="card">
        <div className="card-body">
            <div className="flex justify-between items-center">
                <h2 className="card-title">Linked Items</h2>
                <button onClick={() => setIsLinkModalOpen(true)} className="btn btn-secondary btn-sm">
                    <LinkIcon className="h-5 w-5 mr-2" />
                    Link Item
                </button>
            </div>
            <div className="mt-4 space-y-3">
                {goal.links.length > 0 ? goal.links.map(link => (
                    <div key={link.id} className="flex justify-between items-center bg-gray-50 p-3 rounded-lg">
                        <div>
                            <p className="font-semibold">{link.asset?.name || link.portfolio?.name}</p>
                            <p className="text-sm text-gray-500">{link.asset ? `Asset: ${link.asset.ticker_symbol}` : 'Portfolio'}</p>
                        </div>
                        <button
                            onClick={() => handleUnlink(link.id)}
                            className="btn btn-ghost btn-sm text-red-500 hover:bg-red-100"
                            disabled={deleteGoalLink.isPending}
                        >
                            <TrashIcon className="h-5 w-5" />
                        </button>
                    </div>
                )) : (
                    <p className="text-gray-500 text-center py-4">No items linked to this goal yet.</p>
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

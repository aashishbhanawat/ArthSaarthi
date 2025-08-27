import React, { useState } from 'react';
import { useGoal, useCreateGoalLink, useDeleteGoalLink } from '../../hooks/useGoals';
import AssetLinkModal from '../modals/AssetLinkModal';
import { formatCurrency, formatDate } from '../../utils/formatting';
import { TrashIcon } from '@heroicons/react/24/outline';

interface GoalDetailViewProps {
  goalId: string;
}

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

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>An error occurred: {(error as Error).message}</div>;
  if (!goal) return <div>Goal not found.</div>;

  return (
    <div className="p-4 bg-base-100 rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">{goal.name}</h1>
        <button onClick={() => setIsLinkModalOpen(true)} className="btn btn-primary btn-sm">
          Link Asset/Portfolio
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
            <p className="text-gray-500">Target Amount</p>
            <p className="text-xl font-semibold">{formatCurrency(goal.target_amount)}</p>
        </div>
        <div>
            <p className="text-gray-500">Current Amount</p>
            <p className="text-xl font-semibold">{formatCurrency(goal.current_amount)}</p>
        </div>
        <div>
            <p className="text-gray-500">Target Date</p>
            <p className="text-xl font-semibold">{formatDate(goal.target_date)}</p>
        </div>
      </div>
      <div className="mb-6">
        <p className="text-gray-500">Progress</p>
        <progress className="progress progress-primary w-full" value={goal.progress} max="100"></progress>
        <p className="text-right font-semibold">{goal.progress.toFixed(2)}%</p>
      </div>


      <h2 className="text-xl font-bold mb-4">Linked Items</h2>
      <div className="grid grid-cols-1 gap-4">
        {goal.links.map(link => (
            <div key={link.id} className="card bg-base-200 shadow-md">
                <div className="card-body">
                    <div className="flex justify-between items-center">
                        <div>
                            <h4 className="card-title">{link.portfolio_id ? "Portfolio" : "Asset"}</h4>
                            <p>{link.portfolio_id || link.asset_id}</p>
                        </div>
                        <button onClick={() => handleUnlink(link.id)} className="btn btn-sm btn-circle btn-ghost">
                            <TrashIcon className="h-5 w-5 text-red-500" />
                        </button>
                    </div>
                </div>
            </div>
        ))}
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

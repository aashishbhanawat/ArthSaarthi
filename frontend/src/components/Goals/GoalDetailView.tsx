import React, { useState } from 'react';
import { useGoal, useCreateGoalLink } from '../../hooks/useGoals';
import AssetLinkModal from '../modals/AssetLinkModal';
import { formatCurrency, formatDate } from '../../utils/formatting';

interface GoalDetailViewProps {
  goalId: string;
}

const GoalDetailView: React.FC<GoalDetailViewProps> = ({ goalId }) => {
  const { data: goal, isLoading, error } = useGoal(goalId);
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);
  const createGoalLink = useCreateGoalLink();

  const handleLink = (linkData: { portfolio_id?: string; asset_id?: string }) => {
    createGoalLink.mutate({ goalId, link: { ...linkData, goal_id: goalId } });
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
            <p className="text-gray-500">Target Amount</p>
            <p className="text-xl font-semibold">{formatCurrency(goal.target_amount)}</p>
        </div>
        <div>
            <p className="text-gray-500">Target Date</p>
            <p className="text-xl font-semibold">{formatDate(goal.target_date)}</p>
        </div>
      </div>

      <h2 className="text-xl font-bold mb-4">Linked Items</h2>
      <div className="grid grid-cols-1 gap-4">
        {/* We will map over goal.links here once the backend provides them */}
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

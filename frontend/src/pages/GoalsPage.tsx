import React, { useState } from 'react';
import { useGoals } from '../hooks/useGoals';
import GoalCard from '../components/Goals/GoalCard';
import GoalFormModal from '../components/modals/GoalFormModal';
import AssetLinkModal from '../components/modals/AssetLinkModal';

const GoalsPage: React.FC = () => {
  const { data: goals, isLoading, error } = useGoals();
  const [isGoalFormOpen, setIsGoalFormOpen] = useState(false);
  const [isAssetLinkOpen, setIsAssetLinkOpen] = useState(false);
  const [selectedGoalId, setSelectedGoalId] = useState<string | null>(null);

  const handleLinkAsset = (goalId: string) => {
    setSelectedGoalId(goalId);
    setIsAssetLinkOpen(true);
  };

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>An error occurred: {error.message}</div>;

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Financial Goals</h1>
        <button
          onClick={() => setIsGoalFormOpen(true)}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Create New Goal
        </button>
      </div>

      <div>
        {goals?.map((goal) => (
          <GoalCard key={goal.id} goal={goal} onLinkAsset={handleLinkAsset} />
        ))}
      </div>

      <GoalFormModal
        isOpen={isGoalFormOpen}
        onClose={() => setIsGoalFormOpen(false)}
      />
      {selectedGoalId && (
        <AssetLinkModal
          isOpen={isAssetLinkOpen}
          onClose={() => setIsAssetLinkOpen(false)}
          goalId={selectedGoalId}
        />
      )}
    </div>
  );
};

export default GoalsPage;

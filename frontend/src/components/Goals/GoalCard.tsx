import React, { useState } from 'react';
import { Goal } from '../../types/goal';
import GoalDetailView from './GoalDetailView';

interface GoalCardProps {
  goal: Goal;
  onLinkAsset: (goalId: string) => void;
}

const GoalCard: React.FC<GoalCardProps> = ({ goal, onLinkAsset }) => {
  const [isDetailsVisible, setIsDetailsVisible] = useState(false);

  return (
    <div className="bg-white shadow rounded-lg p-4 mb-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">{goal.name}</h2>
        <div>
          <button
            onClick={() => setIsDetailsVisible(!isDetailsVisible)}
            className="mr-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded"
          >
            {isDetailsVisible ? 'Hide' : 'Show'} Details
          </button>
          <button
            onClick={() => onLinkAsset(goal.id)}
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
            data-testid={`link-asset-button-${goal.id}`}
          >
            Link Asset
          </button>
        </div>
      </div>
      {isDetailsVisible && <GoalDetailView goal={goal} />}
    </div>
  );
};

export default GoalCard;

import React from 'react';
import { Goal } from '../../types/goal';

interface GoalCardProps {
  goal: Goal;
}

const GoalCard: React.FC<GoalCardProps> = ({ goal }) => {
  return (
    <div className="bg-white shadow rounded-lg p-4 mb-4">
      <h2 className="text-xl font-bold">{goal.name}</h2>
      {/* More details will be added here */}
    </div>
  );
};

export default GoalCard;

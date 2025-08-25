import React from 'react';
import { Goal } from '../../types/goal';
import { formatCurrency, formatDate } from '../../utils/formatting';

interface GoalCardProps {
  goal: Goal;
  onEdit: (goal: Goal) => void;
  onDelete: (goal: Goal) => void;
}

const GoalCard: React.FC<GoalCardProps> = ({ goal, onEdit, onDelete }) => {
  // Progress calculation will be implemented in a later phase.
  // For now, we'll use a placeholder value.
  const currentAmount = 0; // Placeholder
  const progress = goal.target_amount > 0 ? (currentAmount / goal.target_amount) * 100 : 0;

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-4">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-xl font-bold text-gray-800">{goal.name}</h3>
          <p className="text-sm text-gray-500">
            Target: {formatCurrency(goal.target_amount)} by {formatDate(goal.target_date)}
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => onEdit(goal)}
            className="text-blue-500 hover:text-blue-700"
            aria-label={`Edit goal ${goal.name}`}
          >
            Edit
          </button>
          <button
            onClick={() => onDelete(goal)}
            className="text-red-500 hover:text-red-700"
            aria-label={`Delete goal ${goal.name}`}
          >
            Delete
          </button>
        </div>
      </div>

      <div className="mt-4">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700">
            Progress ({progress.toFixed(2)}%)
          </span>
          <span className="text-sm font-medium text-gray-700">
            {formatCurrency(currentAmount)} / {formatCurrency(goal.target_amount)}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div
            className="bg-blue-600 h-4 rounded-full"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default GoalCard;

import React from 'react';
import { Link } from 'react-router-dom';
import { Goal } from '../../types/goal';
import { formatCurrency, formatDate } from '../../utils/formatting';

interface GoalCardProps {
  goal: Goal;
  onEdit: (goal: Goal) => void;
  onDelete: (goal: Goal) => void;
}

const GoalCard: React.FC<GoalCardProps> = ({ goal, onEdit, onDelete }) => {
  const currentAmount = goal.current_value ?? 0;
  const progress = goal.progress ?? 0;

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-4 flex justify-between items-start">
      <Link to={`/goals/${goal.id}`} className="flex-grow">
        <div>
          <h3 className="text-xl font-bold text-gray-800 hover:text-blue-600">{goal.name}</h3>
          <p className="text-sm text-gray-500">
            Target: {formatCurrency(goal.target_amount)} by {formatDate(goal.target_date)}
          </p>
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
      </Link>
      <div className="flex flex-col space-y-2 ml-4">
        <button
          onClick={(e) => { e.stopPropagation(); onEdit(goal); }}
          className="btn btn-secondary btn-sm"
          aria-label={`Edit goal ${goal.name}`}
        >
          Edit
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(goal); }}
          className="btn btn-danger btn-sm"
          aria-label={`Delete goal ${goal.name}`}
        >
          Delete
        </button>
      </div>
    </div>
  );
};

export default GoalCard;

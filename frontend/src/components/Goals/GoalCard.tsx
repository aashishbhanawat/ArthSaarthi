import React from 'react';
import { Goal } from '../../types/goal';
import { formatCurrency, formatDate } from '../../utils/formatting';

interface GoalCardProps {
  goal: Goal;
  onEdit: (goal: Goal) => void;
  onDelete: (id: string) => void;
  onSelect: (id: string) => void;
}

const GoalCard: React.FC<GoalCardProps> = ({ goal, onEdit, onDelete, onSelect }) => {
  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <h2 className="card-title">{goal.name}</h2>
        <p>Target: {formatCurrency(goal.target_amount)}</p>
        <p>Date: {formatDate(goal.target_date)}</p>
        <div className="card-actions justify-end">
          <button onClick={() => onSelect(goal.id)} className="btn btn-sm btn-outline">
            View
          </button>
          <button onClick={() => onEdit(goal)} className="btn btn-sm btn-outline btn-primary">
            Edit
          </button>
          <button onClick={() => onDelete(goal.id)} className="btn btn-sm btn-outline btn-error">
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};

export default GoalCard;

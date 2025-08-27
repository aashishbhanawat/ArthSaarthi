import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Goal } from '../../types/goal';
import { useDeleteGoal } from '../../hooks/useGoals';
import DeleteGoalModal from './DeleteGoalModal';
import { TrashIcon } from '@heroicons/react/24/outline';

interface GoalListProps {
  goals: Goal[];
}

const GoalList: React.FC<GoalListProps> = ({ goals }) => {
  const [isModalOpen, setModalOpen] = useState(false);
  const [goalToDelete, setGoalToDelete] = useState<Goal | null>(null);
  const deleteGoalMutation = useDeleteGoal();

  const handleDeleteClick = (goal: Goal) => {
    setGoalToDelete(goal);
    setModalOpen(true);
  };

  const handleConfirmDelete = () => {
    if (goalToDelete) {
      deleteGoalMutation.mutate(goalToDelete.id, {
        onSuccess: () => {
          setModalOpen(false);
          setGoalToDelete(null);
        },
      });
    }
  };

  if (goals.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <h2 className="text-xl font-semibold text-gray-700">No goals yet.</h2>
        <p className="text-gray-500 mt-2">Click "Create Goal" to get started with your financial planning.</p>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul role="list" className="divide-y divide-gray-200">
          {goals.map((goal) => (
            <li key={goal.id} className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <Link to={`/goals/${goal.id}`} className="block hover:bg-gray-50 -m-4 p-4 flex-grow">
                  <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-indigo-600 truncate">{goal.name}</p>
                      <p className="mt-1 flex items-center text-sm text-gray-500">
                        <span>Target: ${goal.target_amount.toLocaleString()}</span>
                        <span className="mx-2">|</span>
                        <span>Date: {new Date(goal.target_date).toLocaleDateString()}</span>
                      </p>
                  </div>
                </Link>
                <div className="ml-4 flex-shrink-0">
                  <button
                    onClick={() => handleDeleteClick(goal)}
                    className="btn btn-sm btn-ghost text-red-600 hover:bg-red-50"
                    disabled={deleteGoalMutation.isPending && goalToDelete?.id === goal.id}
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
      <DeleteGoalModal
        isOpen={isModalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleConfirmDelete}
        goalName={goalToDelete?.name || ''}
        isPending={deleteGoalMutation.isPending}
      />
    </>
  );
};

export default GoalList;

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Goal } from '../../types/goal';
import { useDeleteGoal } from '../../hooks/useGoals';
import DeleteGoalModal from './DeleteGoalModal';
import { TrashIcon } from '@heroicons/react/24/outline';
import { useQueryClient } from '@tanstack/react-query';
import { usePrivacySensitiveCurrency, formatDate } from '../../utils/formatting';

interface GoalListProps {
  goals: Goal[];
}

const GoalList: React.FC<GoalListProps> = ({ goals }) => {
  const queryClient = useQueryClient();
  const [isModalOpen, setModalOpen] = useState(false);
  const [goalToDelete, setGoalToDelete] = useState<Goal | null>(null);
  const deleteGoalMutation = useDeleteGoal();
  const formatCurrency = usePrivacySensitiveCurrency();

  const handleDeleteClick = (goal: Goal) => {
    setGoalToDelete(goal);
    setModalOpen(true);
  };

  const handleConfirmDelete = () => {
    if (goalToDelete) {
      deleteGoalMutation.mutate(goalToDelete.id, {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['goals'] });
          setModalOpen(false);
          setGoalToDelete(null);
        },
      });
    }
  };

  if (goals.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-200">No goals yet.</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-2">Click "Create Goal" to get started with your financial planning.</p>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
        <ul role="list" className="divide-y divide-gray-200 dark:divide-gray-700">
          {goals.map((goal) => (
            <li key={goal.id} className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <Link to={`/goals/${goal.id}`} className="block hover:bg-gray-50 dark:hover:bg-gray-700 -m-4 p-4 flex-grow">
                  <div className="flex-1 min-w-0">
                    <p className="text-xl font-semibold text-blue-600 dark:text-blue-400">{goal.name}</p>
                    <p className="mt-1 flex items-center text-sm text-gray-500 dark:text-gray-400">
                      <span>Target: {formatCurrency(goal.target_amount)}</span>
                      <span className="mx-2">|</span>
                      <span>Date: {formatDate(goal.target_date)}</span>
                    </p>
                  </div>
                </Link>
                <div className="ml-4 flex-shrink-0">
                  <button
                    onClick={() => handleDeleteClick(goal)}
                    className="btn btn-sm btn-ghost text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30"
                    disabled={deleteGoalMutation.isPending && goalToDelete?.id === goal.id}
                    aria-label={`Delete ${goal.name}`}
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

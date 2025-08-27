import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useGoal, useUpdateGoal } from '../hooks/useGoals';
import GoalDetailView from '../components/Goals/GoalDetailView';
import GoalFormModal from '../components/modals/GoalFormModal';
import { GoalUpdate } from '../types/goal';
import { PencilIcon } from '@heroicons/react/24/outline';

const GoalDetailPage: React.FC = () => {
  const { goalId } = useParams<{ goalId: string }>();
  const navigate = useNavigate();
  const { data: goal, isLoading, isError, error } = useGoal(goalId!);
  const updateGoal = useUpdateGoal();

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  if (!goalId) {
    navigate('/goals');
    return null;
  }

  const handleUpdate = (goalData: GoalUpdate) => {
    updateGoal.mutate({ id: goalId, goal: goalData }, {
        onSuccess: () => {
            setIsEditModalOpen(false);
        }
    });
  };

  if (isLoading) return <div className="text-center p-8">Loading goal details...</div>;
  if (isError) return <div className="text-center p-8 text-red-500">Error: {(error as Error).message}</div>;
  if (!goal) return <div className="text-center p-8">Goal not found.</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-8">
        <Link to="/goals" className="text-sm font-medium text-gray-500 hover:text-gray-700">
          &larr; Back to Goals
        </Link>
      </div>

      <div className="flex justify-between items-start mb-6">
        <div>
            <h1 className="text-3xl font-bold">{goal.name}</h1>
            <p className="text-gray-500 mt-1">
                Target: ${goal.target_amount.toLocaleString()} by {new Date(goal.target_date).toLocaleDateString()}
            </p>
        </div>
        <div className="flex space-x-2">
          <button onClick={() => setIsEditModalOpen(true)} className="btn btn-secondary">
            <PencilIcon className="h-5 w-5 mr-2" />
            Edit
          </button>
        </div>
      </div>

      <GoalDetailView goalId={goalId} />

      {isEditModalOpen && (
        <GoalFormModal
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          onSubmit={handleUpdate}
          goal={goal}
        />
      )}
    </div>
  );
};

export default GoalDetailPage;

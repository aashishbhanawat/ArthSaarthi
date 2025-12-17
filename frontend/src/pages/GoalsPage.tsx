import React, { useState } from 'react';
import { useGoals, useCreateGoal } from '../hooks/useGoals';
import GoalList from '../components/Goals/GoalList';
import GoalFormModal from '../components/modals/GoalFormModal';
import { GoalCreate, GoalUpdate } from '../types/goal';

const GoalsPage: React.FC = () => {
  const { data: goals, isLoading, isError, error } = useGoals();
  const createGoal = useCreateGoal();

  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleSubmit = (goalData: GoalCreate | GoalUpdate) => {
    createGoal.mutate(goalData as GoalCreate, {
      onSuccess: () => {
        setIsModalOpen(false);
      }
    });
  };

  if (isLoading) return <div className="text-center p-8">Loading goals...</div>;
  if (isError) return <div className="text-center p-8 text-red-500">Error: {(error as Error).message}</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Goals</h1>
        <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
          Create Goal
        </button>
      </div>

      <GoalList goals={goals || []} />

      <GoalFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSubmit}
      />
    </div>
  );
};

export default GoalsPage;

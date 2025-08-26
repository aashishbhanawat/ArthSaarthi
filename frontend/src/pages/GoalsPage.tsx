import React, { useState } from 'react';
import { useGoals, useCreateGoal, useUpdateGoal, useDeleteGoal } from '../hooks/useGoals';
import GoalCard from '../components/Goals/GoalCard';
import GoalFormModal from '../components/modals/GoalFormModal';
import { Goal, GoalCreate, GoalUpdate } from '../types/goal';
import { PlusIcon } from '@heroicons/react/24/solid';

const GoalsPage: React.FC = () => {
  const { data: goals, isLoading, error } = useGoals();
  const createGoal = useCreateGoal();
  const updateGoal = useUpdateGoal();
  const deleteGoal = useDeleteGoal();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);

  const handleCreate = () => {
    setEditingGoal(null);
    setIsModalOpen(true);
  };

  const handleEdit = (goal: Goal) => {
    setEditingGoal(goal);
    setIsModalOpen(true);
  };

  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this goal?')) {
      deleteGoal.mutate(id);
    }
  };

  const handleSubmit = (goalData: GoalCreate | GoalUpdate) => {
    if (editingGoal) {
      updateGoal.mutate({ id: editingGoal.id, goal: goalData as GoalUpdate });
    } else {
      createGoal.mutate(goalData as GoalCreate);
    }
  };

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>An error occurred: {(error as Error).message}</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Your Goals</h1>
        <button onClick={handleCreate} className="btn btn-primary">
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Goal
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {goals?.map((goal) => (
          <GoalCard
            key={goal.id}
            goal={goal}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))}
      </div>

      {goals?.length === 0 && (
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold">No goals yet.</h2>
          <p className="text-gray-500">Click "Create Goal" to get started.</p>
        </div>
      )}

      <GoalFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSubmit}
        goal={editingGoal}
      />
    </div>
  );
};

export default GoalsPage;

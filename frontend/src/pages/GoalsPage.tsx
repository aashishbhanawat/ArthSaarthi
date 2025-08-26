import React, { useState } from 'react';
import { useGoals, useDeleteGoal } from '../hooks/useGoals';
import GoalCard from '../components/Goals/GoalCard';
import GoalFormModal from '../components/modals/GoalFormModal';
import { Goal } from '../../types/goal';
import { DeleteConfirmationModal } from '../components/common/DeleteConfirmationModal';

const GoalsPage: React.FC = () => {
  const { data: goals, isLoading, isError, error } = useGoals();
  const [isFormModalOpen, setFormModalOpen] = useState(false);
  const [isDeleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<Goal | undefined>(undefined);

  const deleteGoalMutation = useDeleteGoal();

  const handleCreate = () => {
    setSelectedGoal(undefined);
    setFormModalOpen(true);
  };

  const handleEdit = (goal: Goal) => {
    setSelectedGoal(goal);
    setFormModalOpen(true);
  };

  const handleDelete = (goal: Goal) => {
    setSelectedGoal(goal);
    setDeleteModalOpen(true);
  };

  const confirmDelete = () => {
    if (selectedGoal) {
      deleteGoalMutation.mutate(selectedGoal.id, {
        onSuccess: () => {
          setDeleteModalOpen(false);
          setSelectedGoal(undefined);
        },
      });
    }
  };

  if (isLoading) return <div className="text-center p-8">Loading goals...</div>;
  if (isError) return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Financial Goals</h1>
        <button onClick={handleCreate} className="btn btn-primary">
          Create New Goal
        </button>
      </div>

      {goals && goals.length > 0 ? (
        goals.map((goal) => (
          <GoalCard
            key={goal.id}
            goal={goal}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))
      ) : (
        <div className="text-center p-8 bg-gray-100 rounded-lg">
          <p className="text-gray-500">You haven't set any goals yet. Get started by creating one!</p>
        </div>
      )}

      <GoalFormModal
        isOpen={isFormModalOpen}
        onClose={() => setFormModalOpen(false)}
        goal={selectedGoal}
      />

      <DeleteConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        title="Delete Goal"
        message={`Are you sure you want to delete the goal "${selectedGoal?.name}"? This action cannot be undone.`}
        isPending={deleteGoalMutation.isPending}
      />
    </div>
  );
};

export default GoalsPage;

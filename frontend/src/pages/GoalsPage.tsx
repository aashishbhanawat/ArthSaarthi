import React, { useState } from 'react';
import { useGoals } from '../hooks/useGoals';
import GoalCard from '../components/Goals/GoalCard';
import GoalFormModal from '../components/modals/GoalFormModal';

const GoalsPage: React.FC = () => {
  const { data: goals, isLoading, error } = useGoals();
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>An error occurred: {error.message}</div>;

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Financial Goals</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Create New Goal
        </button>
      </div>

      <div>
        {goals?.map((goal) => (
          <GoalCard key={goal.id} goal={goal} />
        ))}
      </div>

      <GoalFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
};

export default GoalsPage;

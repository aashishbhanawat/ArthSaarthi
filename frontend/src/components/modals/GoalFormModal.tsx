import React, { useState } from 'react';
import { useCreateGoal } from '../../hooks/useGoals';
import { GoalCreate } from '../../types/goal';

interface GoalFormModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const GoalFormModal: React.FC<GoalFormModalProps> = ({ isOpen, onClose }) => {
  const [name, setName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const createGoal = useCreateGoal();

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const goalData: GoalCreate = {
      name,
      target_amount: parseFloat(targetAmount),
      target_date: targetDate,
    };
    createGoal.mutate(goalData);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">
      <div className="bg-white p-6 rounded-lg">
        <h2 className="text-2xl font-bold mb-4">Create Goal</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="name" className="block text-gray-700">Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full p-2 border rounded"
              required
            />
          </div>
          <div className="mb-4">
            <label htmlFor="targetAmount" className="block text-gray-700">Target Amount</label>
            <input
              id="targetAmount"
              type="number"
              value={targetAmount}
              onChange={(e) => setTargetAmount(e.target.value)}
              className="w-full p-2 border rounded"
              required
            />
          </div>
          <div className="mb-4">
            <label htmlFor="targetDate" className="block text-gray-700">Target Date</label>
            <input
              id="targetDate"
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="w-full p-2 border rounded"
              required
            />
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-300 rounded">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 bg-blue-500 text-white rounded">
              Create Goal
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default GoalFormModal;

import React, { useState, useEffect } from 'react';
import { Goal, GoalCreate, GoalUpdate } from '../../types/goal';

interface GoalFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (goal: GoalCreate | GoalUpdate) => void;
  goal?: Goal | null;
  isPending?: boolean;
  error?: Error | null;
}

const GoalFormModal: React.FC<GoalFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  goal,
  isPending = false,
  error = null,
}) => {
  const [name, setName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const isEditMode = !!goal;

  useEffect(() => {
    if (isOpen) {
      setName(isEditMode ? goal.name : '');
      setTargetAmount(isEditMode ? goal.target_amount.toString() : '');
      // Format date for input type='date' which requires YYYY-MM-DD
      setTargetDate(isEditMode ? new Date(goal.target_date).toISOString().split('T')[0] : '');
    }
  }, [isOpen, isEditMode, goal]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim() && targetAmount && targetDate) {
      const goalData = {
        name,
        target_amount: parseFloat(targetAmount),
        target_date: targetDate,
      };
      onSubmit(goalData);
      onClose(); // Add this back
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content max-w-md">
        <div className="modal-header">
          <h2 className="text-2xl font-bold">
            {isEditMode ? 'Edit Goal' : 'Create New Goal'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="goal-name" className="form-label">
                Goal Name
              </label>
              <input
                id="goal-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="form-input"
                placeholder="E.g., Buy a house"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="goal-target-amount" className="form-label">
                Target Amount
              </label>
              <input
                id="goal-target-amount"
                type="number"
                value={targetAmount}
                onChange={(e) => setTargetAmount(e.target.value)}
                className="form-input"
                placeholder="E.g., 50000"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="goal-target-date" className="form-label">
                Target Date
              </label>
              <input
                id="goal-target-date"
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                className="form-input"
                required
              />
            </div>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                    <span className="block sm:inline">Error: {error.message}</span>
                </div>
            )}

            <div className="flex items-center justify-end pt-4">
              <button type="button" onClick={onClose} className="btn btn-secondary mr-2" disabled={isPending}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={isPending || !name.trim() || !targetAmount || !targetDate}>
                {isPending ? (isEditMode ? 'Saving...' : 'Creating...') : (isEditMode ? 'Save Changes' : 'Create Goal')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default GoalFormModal;

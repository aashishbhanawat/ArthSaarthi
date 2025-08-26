import React, { useState, useEffect } from 'react';
import { Goal, GoalCreate, GoalUpdate } from '../../types/goal';

interface GoalFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (goal: GoalCreate | GoalUpdate) => void;
  goal?: Goal | null; // Provide for editing
}

const GoalFormModal: React.FC<GoalFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  goal,
}) => {
  const [name, setName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const isEditMode = !!goal;

  useEffect(() => {
    if (isOpen) {
      setName(isEditMode ? goal.name : '');
      setTargetAmount(isEditMode ? goal.target_amount.toString() : '');
      setTargetDate(isEditMode ? goal.target_date : '');
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
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box">
        <h3 className="font-bold text-lg">
          {isEditMode ? 'Edit Goal' : 'Create New Goal'}
        </h3>
        <form onSubmit={handleSubmit}>
          <div className="form-control w-full py-2">
            <label className="label" htmlFor="goalName">
              <span className="label-text">Goal Name</span>
            </label>
            <input
              id="goalName"
              type="text"
              placeholder="E.g., Buy a house"
              className="input input-bordered w-full"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="form-control w-full py-2">
            <label className="label" htmlFor="targetAmount">
              <span className="label-text">Target Amount</span>
            </label>
            <input
              id="targetAmount"
              type="number"
              placeholder="E.g., 50000"
              className="input input-bordered w-full"
              value={targetAmount}
              onChange={(e) => setTargetAmount(e.target.value)}
              required
            />
          </div>
          <div className="form-control w-full py-2">
            <label className="label" htmlFor="targetDate">
              <span className="label-text">Target Date</span>
            </label>
            <input
              id="targetDate"
              type="date"
              className="input input-bordered w-full"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              required
            />
          </div>
          <div className="modal-action mt-4">
            <button type="button" onClick={onClose} className="btn btn-ghost">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={!name.trim() || !targetAmount || !targetDate}>
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default GoalFormModal;

import React, { useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { useCreateGoal, useUpdateGoal } from '../../hooks/useGoals';
import { Goal, GoalCreate, GoalUpdate } from '../../types/goal';

interface GoalFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  goal?: Goal;
}

type FormValues = {
  name: string;
  target_amount: number;
  target_date: string;
};

const GoalFormModal: React.FC<GoalFormModalProps> = ({ isOpen, onClose, goal }) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>();

  const createGoalMutation = useCreateGoal();
  const updateGoalMutation = useUpdateGoal();

  const isEditMode = !!goal;

  useEffect(() => {
    if (goal) {
      reset({
        name: goal.name,
        target_amount: goal.target_amount,
        target_date: goal.target_date.split('T')[0], // Format date for input
      });
    } else {
      reset({
        name: '',
        target_amount: 0,
        target_date: '',
      });
    }
  }, [goal, reset]);

  const onSubmit: SubmitHandler<FormValues> = (data) => {
    const goalData: GoalCreate | GoalUpdate = {
      ...data,
      target_amount: Number(data.target_amount),
    };

    if (isEditMode) {
      updateGoalMutation.mutate({ id: goal.id, data: goalData }, {
        onSuccess: () => {
          reset();
          onClose();
        },
      });
    } else {
      createGoalMutation.mutate(goalData as GoalCreate, {
        onSuccess: () => {
          reset();
          onClose();
        },
      });
    }
  };

  if (!isOpen) return null;

  const isPending = createGoalMutation.isPending || updateGoalMutation.isPending;

  return (
    <div className="modal-overlay">
      <div className="modal-content max-w-lg">
        <div className="modal-header">
          <h2 className="text-2xl font-bold">{isEditMode ? 'Edit Goal' : 'Create New Goal'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="form-group">
              <label htmlFor="goal-name" className="form-label">Goal Name</label>
              <input
                id="goal-name"
                type="text"
                {...register('name', { required: 'Name is required' })}
                className="form-input"
              />
              {errors.name && <p className="form-error">{errors.name.message}</p>}
            </div>

            <div className="form-group">
              <label htmlFor="target-amount" className="form-label">Target Amount</label>
              <input
                id="target-amount"
                type="number"
                step="0.01"
                {...register('target_amount', { required: 'Target amount is required', valueAsNumber: true })}
                className="form-input"
              />
              {errors.target_amount && <p className="form-error">{errors.target_amount.message}</p>}
            </div>

            <div className="form-group">
              <label htmlFor="target-date" className="form-label">Target Date</label>
              <input
                id="target-date"
                type="date"
                {...register('target_date', { required: 'Target date is required' })}
                className="form-input"
              />
              {errors.target_date && <p className="form-error">{errors.target_date.message}</p>}
            </div>

            {(createGoalMutation.isError || updateGoalMutation.isError) && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                <span className="block sm:inline">
                  Error: {createGoalMutation.error?.message || updateGoalMutation.error?.message}
                </span>
              </div>
            )}

            <div className="flex items-center justify-end pt-4">
              <button type="button" onClick={onClose} className="btn btn-secondary mr-2" disabled={isPending}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={isPending}>
                {isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default GoalFormModal;

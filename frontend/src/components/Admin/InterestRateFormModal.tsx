import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { HistoricalInterestRate, HistoricalInterestRateCreate, HistoricalInterestRateUpdate } from '../../types/interestRate';
import { useCreateInterestRate, useUpdateInterestRate } from '../../hooks/useInterestRates';

interface InterestRateFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  rateToEdit: HistoricalInterestRate | null;
}

const InterestRateFormModal: React.FC<InterestRateFormModalProps> = ({ isOpen, onClose, rateToEdit }) => {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<HistoricalInterestRateCreate | HistoricalInterestRateUpdate>();
  const [apiError, setApiError] = useState<string | null>(null);

  const createMutation = useCreateInterestRate();
  const updateMutation = useUpdateInterestRate();

  const isEditing = !!rateToEdit;
  const { isPending } = isEditing ? updateMutation : createMutation;

  useEffect(() => {
    if (isOpen) {
      if (isEditing && rateToEdit) {
        reset({
          scheme_name: rateToEdit.scheme_name,
          start_date: rateToEdit.start_date,
          end_date: rateToEdit.end_date,
          rate: rateToEdit.rate,
        });
      } else {
        reset({ scheme_name: 'PPF', start_date: '', end_date: '', rate: 0 });
      }
    } else {
      reset();
      setApiError(null);
    }
  }, [isOpen, rateToEdit, isEditing, reset]);

  const onSubmit = (data: HistoricalInterestRateCreate | HistoricalInterestRateUpdate) => {
    setApiError(null);
    const mutationOptions = {
      onSuccess: () => onClose(),
      onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
        setApiError(error.response?.data?.detail ?? 'An unexpected error occurred.');
      }
    };

    if (isEditing && rateToEdit) {
      updateMutation.mutate({ rateId: rateToEdit.id, rateData: data }, mutationOptions);
    } else {
      createMutation.mutate(data as HistoricalInterestRateCreate, mutationOptions);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div role="dialog" aria-modal="true" aria-labelledby="rate-form-modal-title" className="modal-content max-w-md">
        <div className="modal-header">
          <h2 id="rate-form-modal-title" className="text-2xl font-bold">{isEditing ? 'Edit Interest Rate' : 'Add New Interest Rate'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="form-group">
              <label htmlFor="scheme_name" className="form-label">Scheme Name</label>
              <input id="scheme_name" type="text" {...register('scheme_name', { required: 'Scheme name is required' })} className="form-input" required disabled={isPending} />
              {errors.scheme_name && <p className="form-error">{errors.scheme_name.message}</p>}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="form-group">
                <label htmlFor="start_date" className="form-label">Start Date</label>
                <input id="start_date" type="date" {...register('start_date', { required: 'Start date is required' })} className="form-input" required disabled={isPending} />
                {errors.start_date && <p className="form-error">{errors.start_date.message}</p>}
              </div>
              <div className="form-group">
                <label htmlFor="end_date" className="form-label">End Date (optional)</label>
                <input id="end_date" type="date" {...register('end_date')} className="form-input" disabled={isPending} />
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="rate" className="form-label">Interest Rate (%)</label>
              <input id="rate" type="number" step="0.01" {...register('rate', { required: 'Rate is required', valueAsNumber: true })} className="form-input" required disabled={isPending} />
              {errors.rate && <p className="form-error">{errors.rate.message}</p>}
            </div>

            {apiError && (
              <div className="alert alert-error" role="alert">
                <span className="block sm:inline">{apiError}</span>
              </div>
            )}

            <div className="flex items-center justify-end pt-4">
              <button type="button" onClick={onClose} className="btn btn-secondary mr-2" disabled={isPending}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={isPending}>
                {isPending ? 'Saving...' : (isEditing ? 'Save Changes' : 'Create Rate')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default InterestRateFormModal;
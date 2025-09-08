import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { HistoricalInterestRate, HistoricalInterestRateCreate } from '../../types/asset';

interface InterestRateFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (data: HistoricalInterestRateCreate) => void;
    initialData?: HistoricalInterestRate;
}

const InterestRateFormModal: React.FC<InterestRateFormModalProps> = ({ isOpen, onClose, onSubmit, initialData }) => {
    const { register, handleSubmit, reset, formState: { errors } } = useForm<HistoricalInterestRateCreate>();

    useEffect(() => {
        if (initialData) {
            reset({
                ...initialData,
                start_date: new Date(initialData.start_date).toISOString().split('T')[0],
                end_date: new Date(initialData.end_date).toISOString().split('T')[0],
            });
        } else {
            reset({
                scheme_name: 'PPF',
                start_date: '',
                end_date: '',
                rate: 0,
            });
        }
    }, [initialData, reset]);

    if (!isOpen) return null;

    return (
        <div className="modal-overlay z-30" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h2 className="text-2xl font-bold mb-4">{initialData ? 'Edit' : 'Add'} Interest Rate</h2>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div>
                        <label htmlFor="scheme_name" className="form-label">Scheme Name</label>
                        <input id="scheme_name" {...register('scheme_name', { required: 'Scheme name is required' })} className="form-input" />
                        {errors.scheme_name && <p className="text-red-500 text-xs italic">{errors.scheme_name.message}</p>}
                    </div>
                    <div>
                        <label htmlFor="start_date" className="form-label">Start Date</label>
                        <input id="start_date" type="date" {...register('start_date', { required: 'Start date is required' })} className="form-input" />
                        {errors.start_date && <p className="text-red-500 text-xs italic">{errors.start_date.message}</p>}
                    </div>
                    <div>
                        <label htmlFor="end_date" className="form-label">End Date</label>
                        <input id="end_date" type="date" {...register('end_date', { required: 'End date is required' })} className="form-input" />
                        {errors.end_date && <p className="text-red-500 text-xs italic">{errors.end_date.message}</p>}
                    </div>
                    <div>
                        <label htmlFor="rate" className="form-label">Rate (%)</label>
                        <input id="rate" type="number" step="0.01" {...register('rate', { required: 'Rate is required', valueAsNumber: true })} className="form-input" />
                        {errors.rate && <p className="text-red-500 text-xs italic">{errors.rate.message}</p>}
                    </div>
                    <div className="flex justify-end space-x-2 pt-4">
                        <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                        <button type="submit" className="btn btn-primary">Save</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default InterestRateFormModal;

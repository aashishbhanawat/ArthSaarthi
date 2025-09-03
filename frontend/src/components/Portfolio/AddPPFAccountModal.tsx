import React from 'react';
import { useForm } from 'react-hook-form';
import { useCreatePpf } from '../../hooks/useFixedIncome';
import { PublicProvidentFundCreate } from '../../types/fixed_income';

interface AddPPFAccountModalProps {
    onClose: () => void;
    isOpen: boolean;
    portfolioId: string;
}

const AddPPFAccountModal: React.FC<AddPPFAccountModalProps> = ({ onClose, isOpen, portfolioId }) => {
    const { register, handleSubmit, formState: { errors } } = useForm<PublicProvidentFundCreate>();
    const createPpfMutation = useCreatePpf();

    const onSubmit = (data: PublicProvidentFundCreate) => {
        createPpfMutation.mutate({ portfolioId, data }, {
            onSuccess: () => {
                onClose();
            },
        });
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay z-30" onClick={onClose}>
            <div role="dialog" aria-modal="true" className="modal-content w-11/12 md:w-3/4 lg:max-w-2xl p-6" onClick={e => e.stopPropagation()}>
                <h2 className="text-2xl font-bold mb-4">Add PPF Account</h2>
                <div className="max-h-[70vh] overflow-y-auto px-2 -mr-2">
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="form-group">
                                <label htmlFor="institution_name" className="form-label">Institution Name</label>
                                <input id="institution_name" {...register('institution_name', { required: "This field is required" })} className="form-input" />
                                {errors.institution_name && <p className="text-red-500 text-xs italic">{errors.institution_name.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="account_number" className="form-label">Account Number (Optional)</label>
                                <input id="account_number" {...register('account_number')} className="form-input" />
                            </div>
                            <div className="form-group">
                                <label htmlFor="opening_date" className="form-label">Opening Date</label>
                                <input id="opening_date" type="date" {...register('opening_date', { required: "This field is required" })} className="form-input" />
                                {errors.opening_date && <p className="text-red-500 text-xs italic">{errors.opening_date.message}</p>}
                            </div>
                             <div className="form-group">
                                <label htmlFor="current_balance" className="form-label">Current Balance</label>
                                <input id="current_balance" type="number" step="any" {...register('current_balance', { required: "This field is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                {errors.current_balance && <p className="text-red-500 text-xs italic">{errors.current_balance.message}</p>}
                            </div>
                        </div>
                        <div className="flex justify-end space-x-4 pt-4">
                            <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                            <button type="submit" className="btn btn-primary" disabled={createPpfMutation.isLoading}>
                                {createPpfMutation.isLoading ? 'Saving...' : 'Save PPF Account'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default AddPPFAccountModal;

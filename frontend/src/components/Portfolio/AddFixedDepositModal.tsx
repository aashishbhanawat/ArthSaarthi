import React from 'react';
import { useForm } from 'react-hook-form';
import { useCreateFixedDeposit } from '../../hooks/useFixedIncome';
import { FixedDepositCreate } from '../../types/fixed_income';

interface AddFixedDepositModalProps {
    onClose: () => void;
    isOpen: boolean;
    portfolioId: string;
}

const AddFixedDepositModal: React.FC<AddFixedDepositModalProps> = ({ onClose, isOpen, portfolioId }) => {
    const { register, handleSubmit, formState: { errors } } = useForm<FixedDepositCreate>();
    const createFixedDepositMutation = useCreateFixedDeposit();

    const onSubmit = (data: FixedDepositCreate) => {
        createFixedDepositMutation.mutate({ portfolioId, data }, {
            onSuccess: () => {
                onClose();
            },
        });
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay z-30" onClick={onClose}>
            <div role="dialog" aria-modal="true" className="modal-content w-11/12 md:w-3/4 lg:max-w-2xl p-6" onClick={e => e.stopPropagation()}>
                <h2 className="text-2xl font-bold mb-4">Add Fixed Deposit</h2>
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
                                <label htmlFor="principal_amount" className="form-label">Principal Amount</label>
                                <input id="principal_amount" type="number" step="any" {...register('principal_amount', { required: "This field is required", valueAsNumber: true, min: { value: 0.01, message: "Must be positive" } })} className="form-input" />
                                {errors.principal_amount && <p className="text-red-500 text-xs italic">{errors.principal_amount.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="interest_rate" className="form-label">Interest Rate (%)</label>
                                <input id="interest_rate" type="number" step="any" {...register('interest_rate', { required: "This field is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                {errors.interest_rate && <p className="text-red-500 text-xs italic">{errors.interest_rate.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="start_date" className="form-label">Start Date</label>
                                <input id="start_date" type="date" {...register('start_date', { required: "This field is required" })} className="form-input" />
                                {errors.start_date && <p className="text-red-500 text-xs italic">{errors.start_date.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="maturity_date" className="form-label">Maturity Date</label>
                                <input id="maturity_date" type="date" {...register('maturity_date', { required: "This field is required" })} className="form-input" />
                                {errors.maturity_date && <p className="text-red-500 text-xs italic">{errors.maturity_date.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="payout_type" className="form-label">Payout Type</label>
                                <select id="payout_type" {...register('payout_type')} className="form-input">
                                    <option value="REINVESTMENT">Re-investment (Cumulative)</option>
                                    <option value="PAYOUT">Payout (Non-cumulative)</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label htmlFor="compounding_frequency" className="form-label">Compounding Frequency</label>
                                <select id="compounding_frequency" {...register('compounding_frequency')} className="form-input">
                                    <option value="MONTHLY">Monthly</option>
                                    <option value="QUARTERLY">Quarterly</option>
                                    <option value="HALF_YEARLY">Half-yearly</option>
                                    <option value="ANNUALLY">Annually</option>
                                    <option value="AT_MATURITY">At Maturity</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex justify-end space-x-4 pt-4">
                            <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                            <button type="submit" className="btn btn-primary" disabled={createFixedDepositMutation.isLoading}>
                                {createFixedDepositMutation.isLoading ? 'Saving...' : 'Save Fixed Deposit'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default AddFixedDepositModal;

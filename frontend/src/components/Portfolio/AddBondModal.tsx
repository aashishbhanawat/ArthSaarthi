import React from 'react';
import { useForm } from 'react-hook-form';
import { useCreateBond } from '../../hooks/useFixedIncome';
import { BondCreate } from '../../types/fixed_income';

interface AddBondModalProps {
    onClose: () => void;
    isOpen: boolean;
    portfolioId: string;
}

const AddBondModal: React.FC<AddBondModalProps> = ({ onClose, isOpen, portfolioId }) => {
    const { register, handleSubmit, formState: { errors } } = useForm<BondCreate>();
    const createBondMutation = useCreateBond();

    const onSubmit = (data: BondCreate) => {
        createBondMutation.mutate({ portfolioId, data }, {
            onSuccess: () => {
                onClose();
            },
        });
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay z-30" onClick={onClose}>
            <div role="dialog" aria-modal="true" className="modal-content w-11/12 md:w-3/4 lg:max-w-2xl p-6" onClick={e => e.stopPropagation()}>
                <h2 className="text-2xl font-bold mb-4">Add Bond</h2>
                <div className="max-h-[70vh] overflow-y-auto px-2 -mr-2">
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="form-group">
                                <label htmlFor="bond_name" className="form-label">Bond Name</label>
                                <input id="bond_name" {...register('bond_name', { required: "This field is required" })} className="form-input" />
                                {errors.bond_name && <p className="text-red-500 text-xs italic">{errors.bond_name.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="isin" className="form-label">ISIN (Optional)</label>
                                <input id="isin" {...register('isin')} className="form-input" />
                            </div>
                            <div className="form-group">
                                <label htmlFor="face_value" className="form-label">Face Value</label>
                                <input id="face_value" type="number" step="any" {...register('face_value', { required: "This field is required", valueAsNumber: true, min: { value: 0.01, message: "Must be positive" } })} className="form-input" />
                                {errors.face_value && <p className="text-red-500 text-xs italic">{errors.face_value.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="coupon_rate" className="form-label">Coupon Rate (%)</label>
                                <input id="coupon_rate" type="number" step="any" {...register('coupon_rate', { required: "This field is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                {errors.coupon_rate && <p className="text-red-500 text-xs italic">{errors.coupon_rate.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="purchase_price" className="form-label">Purchase Price</label>
                                <input id="purchase_price" type="number" step="any" {...register('purchase_price', { required: "This field is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                {errors.purchase_price && <p className="text-red-500 text-xs italic">{errors.purchase_price.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="purchase_date" className="form-label">Purchase Date</label>
                                <input id="purchase_date" type="date" {...register('purchase_date', { required: "This field is required" })} className="form-input" />
                                {errors.purchase_date && <p className="text-red-500 text-xs italic">{errors.purchase_date.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="maturity_date" className="form-label">Maturity Date</label>
                                <input id="maturity_date" type="date" {...register('maturity_date', { required: "This field is required" })} className="form-input" />
                                {errors.maturity_date && <p className="text-red-500 text-xs italic">{errors.maturity_date.message}</p>}
                            </div>
                            <div className="form-group">
                                <label htmlFor="interest_payout_frequency" className="form-label">Interest Payout</label>
                                <select id="interest_payout_frequency" {...register('interest_payout_frequency')} className="form-input">
                                    <option value="ANNUALLY">Annually</option>
                                    <option value="SEMI_ANNUALLY">Semi-Annually</option>
                                </select>
                            </div>
                             <div className="form-group">
                                <label htmlFor="quantity" className="form-label">Quantity</label>
                                <input id="quantity" type="number" {...register('quantity', { required: "This field is required", valueAsNumber: true, min: { value: 1, message: "Must be at least 1" } })} className="form-input" />
                                {errors.quantity && <p className="text-red-500 text-xs italic">{errors.quantity.message}</p>}
                            </div>
                        </div>
                        <div className="flex justify-end space-x-4 pt-4">
                            <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                            <button type="submit" className="btn btn-primary" disabled={createBondMutation.isLoading}>
                                {createBondMutation.isLoading ? 'Saving...' : 'Save Bond'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default AddBondModal;

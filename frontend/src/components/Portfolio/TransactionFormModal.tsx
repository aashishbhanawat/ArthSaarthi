import React, { useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useCreateTransaction } from '../../hooks/usePortfolios';
import { useCheckPpfAccount, useCreatePpfAccountWithContribution } from '../../hooks/useAssets';
import { PpfAccountCreateWithContribution } from '../../types/asset';
import { Transaction, TransactionCreate } from '../../types/portfolio';

interface TransactionFormModalProps {
    portfolioId: string;
    onClose: () => void;
    isOpen: boolean;
    transactionToEdit?: Transaction;
}

type TransactionFormInputs = {
    asset_type: 'Stock' | 'Mutual Fund' | 'PPF Account';
    transaction_type: 'BUY' | 'SELL' | 'CONTRIBUTION';
    quantity: number;
    price_per_unit: number;
    transaction_date: string;
    fees?: number;
    // PPF Create
    institutionName?: string;
    accountNumber?: string;
    openingDate?: string;
    contributionAmount?: number;
    contributionDate?: string;
    // PPF Contribution
    newContributionAmount?: number;
    newContributionDate?: string;
};

const TransactionFormModal: React.FC<TransactionFormModalProps> = ({ portfolioId, onClose, isOpen, transactionToEdit }) => {
    const isEditMode = !!transactionToEdit;
    const { register, handleSubmit, control } = useForm<TransactionFormInputs>({
        defaultValues: { asset_type: 'Stock' }
    });

    const createTransactionMutation = useCreateTransaction();
    const createPpfAccountMutation = useCreatePpfAccountWithContribution();
    const { data: ppfAccount, isLoading: isPpfCheckLoading } = useCheckPpfAccount();

    const [apiError, setApiError] = useState<string | null>(null);
    const assetType = useWatch({ control, name: 'asset_type' });

    const onSubmit = (data: TransactionFormInputs) => {
        const mutationOptions = {
            onSuccess: () => onClose(),
            onError: (error: any) => {
                const errorMessage = error.response?.data?.detail || error.message;
                console.error("API Error:", error.response?.data);
                setApiError(errorMessage);
            },
        };

        if (assetType === 'PPF Account') {
            if (ppfAccount) {
                const payload: TransactionCreate = {
                    asset_id: ppfAccount.id,
                    transaction_type: 'CONTRIBUTION',
                    quantity: data.newContributionAmount!,
                    price_per_unit: 1,
                    transaction_date: new Date(data.newContributionDate!).toISOString(),
                    ticker_symbol: ppfAccount.ticker_symbol,
                };
                createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
            } else {
                const payload: PpfAccountCreateWithContribution = {
                    portfolioId: portfolioId,
                    institutionName: data.institutionName!,
                    accountNumber: data.accountNumber,
                    openingDate: data.openingDate!,
                    contributionAmount: data.contributionAmount!,
                    contributionDate: data.contributionDate!,
                };
                createPpfAccountMutation.mutate(payload, mutationOptions);
            }
        } else {
            // ... (existing logic for Stock and Mutual Fund)
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay z-30" onClick={onClose}>
            <div role="dialog" className="modal-content" onClick={e => e.stopPropagation()}>
                <h2 className="text-2xl font-bold mb-4">{isEditMode ? 'Edit' : 'Add'} Transaction</h2>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    <div className="form-group">
                        <label htmlFor="asset_type" className="form-label">Asset Type</label>
                        <select id="asset_type" {...register('asset_type')} className="form-input" disabled={isEditMode}>
                            <option value="Stock">Stock</option>
                            <option value="Mutual Fund">Mutual Fund</option>
                            <option value="PPF Account">PPF Account</option>
                        </select>
                    </div>

                    {assetType === 'PPF Account' ? (
                        isPpfCheckLoading ? (
                            <div>Loading...</div>
                        ) : ppfAccount ? (
                            // State 2: Existing PPF Account
                            <div>
                                <div className="p-4 border rounded-md bg-gray-50 mb-4">
                                    <h3 className="font-semibold text-lg mb-2">Existing PPF Account</h3>
                                    <p><strong>Institution:</strong> {ppfAccount.name}</p>
                                    <p><strong>Account #:</strong> {ppfAccount.account_number}</p>
                                </div>
                                <h3 className="font-semibold text-lg mb-2">Add New Contribution</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="form-group">
                                        <label htmlFor="newContributionAmount" className="form-label">Amount (₹)</label>
                                        <input id="newContributionAmount" type="number" {...register('newContributionAmount', { required: true, valueAsNumber: true })} className="form-input" />
                                    </div>
                                    <div className="form-group">
                                        <label htmlFor="newContributionDate" className="form-label">Date</label>
                                        <input id="newContributionDate" type="date" {...register('newContributionDate', { required: true })} className="form-input" />
                                    </div>
                                </div>
                            </div>
                        ) : (
                            // State 1: No Existing PPF Account
                            <div>
                                <div className="p-4 border rounded-md mb-4">
                                    <h3 className="font-semibold text-lg mb-2">Create Your PPF Account</h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="form-group col-span-2">
                                            <label htmlFor="institutionName" className="form-label">Institution Name</label>
                                            <input id="institutionName" type="text" {...register('institutionName', { required: true })} className="form-input" />
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="accountNumber" className="form-label">Account Number</label>
                                            <input id="accountNumber" type="text" {...register('accountNumber')} className="form-input" />
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="openingDate" className="form-label">Opening Date</label>
                                            <input id="openingDate" type="date" {...register('openingDate', { required: true })} className="form-input" />
                                        </div>
                                    </div>
                                </div>
                                <div className="p-4 border rounded-md">
                                    <h3 className="font-semibold text-lg mb-2">Add First Contribution</h3>
                                    <div className="grid grid-cols-2 gap-4">
                                         <div className="form-group">
                                            <label htmlFor="contributionAmount" className="form-label">Amount (₹)</label>
                                            <input id="contributionAmount" type="number" {...register('contributionAmount', { required: true, valueAsNumber: true })} className="form-input" />
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="contributionDate" className="form-label">Date</label>
                                            <input id="contributionDate" type="date" {...register('contributionDate', { required: true })} className="form-input" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )
                    ) : (
                        // Existing form for Stock and Mutual Fund
                        <p>Stock/MF form placeholder</p>
                    )}

                    {apiError && <div className="alert alert-error mt-2"><p>{apiError}</p></div>}
                    <div className="flex justify-end space-x-4 pt-4">
                        <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                        <button type="submit" className="btn btn-primary">Save</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default TransactionFormModal;
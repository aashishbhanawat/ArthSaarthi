import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useCreateTransaction, useUpdateTransaction, useCreateFixedDeposit } from '../../hooks/usePortfolios';
import { useAssetSearch, useCreateAsset, useMfSearch, useCheckPpfAccount } from '../../hooks/useAssets';
import { Transaction, TransactionCreate, TransactionUpdate } from '../../types/portfolio';
import { FixedDepositCreate } from '../../types/portfolio';

interface TransactionFormModalProps {
    portfolioId: string;
    onClose: () => void;
    isOpen: boolean;
    transactionToEdit?: Transaction | null;
}

type TransactionFormInputs = {
    asset_type: 'Stock' | 'Mutual Fund' | 'Fixed Deposit' | 'PPF Account';
    asset_id: string;
    ticker_symbol: string;
    name: string;
    transaction_type: 'BUY' | 'SELL' | 'CONTRIBUTION';
    quantity: number;
    price_per_unit: number;
    transaction_date: string;
    fees?: number;
    // For creating a new asset
    new_asset_name?: string;
    new_asset_ticker?: string;
    // For mutual funds
    mf_name?: string;
    mf_ticker_symbol?: string;
    // For fixed deposits
    fd_name?: string;
    fd_account_number?: string;
    fd_principal_amount?: number;
    fd_interest_rate?: number;
    fd_start_date?: string;
    fd_maturity_date?: string;
    fd_compounding_frequency?: 'Annually' | 'Semi-Annually' | 'Quarterly' | 'Monthly';
    fd_interest_payout?: 'Cumulative' | 'Monthly' | 'Quarterly' | 'Semi-Annually' | 'Annually';
};


const TransactionFormModal: React.FC<TransactionFormModalProps> = ({ portfolioId, onClose, isOpen, transactionToEdit }) => {
    const isEditMode = !!transactionToEdit;
    const { register, handleSubmit, setValue, watch, reset } = useForm<TransactionFormInputs>({
        defaultValues: {
            ...transactionToEdit,
            asset_type: 'Stock',
            transaction_date: transactionToEdit ? new Date(transactionToEdit.transaction_date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
        }
    });

    // Mutations and Queries
    const createTransactionMutation = useCreateTransaction();
    const updateTransactionMutation = useUpdateTransaction();
    const createAssetMutation = useCreateAsset();
    const createFixedDepositMutation = useCreateFixedDeposit();
    const { data: ppfAccount, isLoading: isPpfCheckLoading } = useCheckPpfAccount();

    // Local State
    const [searchQuery, setSearchQuery] = useState('');
    const [mfSearchQuery, setMfSearchQuery] = useState('');
    const [isCreatingNewAsset, setIsCreatingNewAsset] = useState(false);
    const { data: searchResults, isLoading: isSearchLoading } = useAssetSearch(searchQuery);
    const { data: mfSearchResults, isLoading: isMfSearchLoading } = useMfSearch(mfSearchQuery);
    const assetType = watch('asset_type');
    const [apiError, setApiError] = useState<string | null>(null);

    // Effect to reset form when opened for editing or creating
    useEffect(() => {
        if (!isOpen) {
            setIsCreatingNewAsset(false);
            setSearchQuery('');
            setMfSearchQuery('');
            setApiError(null);
        }
        if (transactionToEdit) {
            reset({
                ...transactionToEdit,
                asset_type: transactionToEdit?.asset?.asset_type === 'Mutual Fund' ? 'Mutual Fund' : 'Stock',
                transaction_date: new Date(transactionToEdit.transaction_date).toISOString().split('T')[0],
                asset_id: transactionToEdit.asset_id,
                ticker_symbol: transactionToEdit.asset.ticker_symbol,
                name: transactionToEdit.asset.name,
            });
        } else {
            reset({
                asset_type: 'Stock',
                transaction_type: 'BUY',
                transaction_date: new Date().toISOString().split('T')[0],
                fd_compounding_frequency: 'Annually',
                fd_interest_payout: 'Cumulative'
            });
        }
    }, [transactionToEdit, isOpen, reset]);


    const onSubmit = async (data: TransactionFormInputs) => {
        setApiError(null);
        const mutationOptions = {
            onSuccess: () => {
                onClose();
            },
            onError: (error: { response?: { data?: { detail?: string } }, message?: string }) => {
                const errorMessage = error.response?.data?.detail || error.message || 'An unexpected error occurred.';
                console.error("API Error:", error.response?.data);
                setApiError(errorMessage);
            }
        };

        if (assetType === 'PPF Account') {
            if (ppfAccount) {
                const payload: TransactionCreate = {
                    asset_id: ppfAccount.id,
                    transaction_type: 'CONTRIBUTION',
                    quantity: data.quantity,
                    price_per_unit: 1,
                    transaction_date: new Date(data.transaction_date).toISOString(),
                };
                createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
            } else {
                setApiError("Please create a PPF account first.");
            }
            return;
        }


        if (assetType === 'Fixed Deposit') {
            const fdData: FixedDepositCreate = {
                name: data.fd_name!,
                account_number: data.fd_account_number,
                principal_amount: data.fd_principal_amount!,
                interest_rate: data.fd_interest_rate!,
                start_date: data.fd_start_date!,
                maturity_date: data.fd_maturity_date!,
                compounding_frequency: data.fd_compounding_frequency!,
                interest_payout: data.fd_interest_payout!,
            };
            createFixedDepositMutation.mutate({ portfolioId, data: fdData }, mutationOptions);
            return;
        }

        const transactionData: Partial<TransactionCreate & TransactionUpdate> = {
            transaction_type: data.transaction_type,
            quantity: data.quantity,
            price_per_unit: data.price_per_unit,
            transaction_date: new Date(data.transaction_date).toISOString(),
            fees: data.fees,
        };

        if (isEditMode) {
            updateTransactionMutation.mutate({
                portfolioId,
                transactionId: transactionToEdit!.id,
                data: transactionData as TransactionUpdate
            }, mutationOptions);
        } else {
            let finalAssetId = data.asset_id;
            if (assetType === 'Mutual Fund') {
                transactionData.ticker_symbol = data.mf_ticker_symbol;
                transactionData.asset_type = 'Mutual Fund';
            } else if (isCreatingNewAsset) {
                try {
                    const newAsset = await createAssetMutation.mutateAsync({ name: data.new_asset_name!, ticker_symbol: data.new_asset_ticker! });
                    finalAssetId = newAsset.id;
                } catch (error: { response?: { data?: { detail?: string } } }) {
                    setApiError(error.response?.data?.detail || 'Failed to create new asset.');
                    return;
                }
            }
            transactionData.asset_id = finalAssetId;
            createTransactionMutation.mutate({ portfolioId, data: transactionData as TransactionCreate }, mutationOptions);
        }
    };


    if (!isOpen) return null;

    const renderAssetSelection = () => {
        if (assetType === 'PPF Account') {
            if (isPpfCheckLoading) return <div>Checking for existing PPF Account...</div>;
            if (ppfAccount) {
                return (
                    <div className="form-group">
                        <label className="form-label">PPF Account</label>
                        <input type="text" value={ppfAccount.name} className="form-input" disabled />
                    </div>
                );
            }
            return (
                <div className="alert alert-info">
                    <p>You do not have a PPF account yet. Please create one from the assets page.</p>
                </div>
            );
        } else if (assetType === 'Mutual Fund') {
            return (
                <div className="form-group">
                    <label htmlFor="mf_name" className="form-label">Asset</label>
                    <input
                        id="mf_name"
                        type="text"
                        className="form-input"
                        placeholder="Search for a Mutual Fund"
                        onChange={(e) => setMfSearchQuery(e.target.value)}
                        disabled={isEditMode}
                    />
                    {isMfSearchLoading && <div>Searching...</div>}
                    {mfSearchResults && mfSearchQuery && (
                        <ul className="autocomplete-results">
                            {mfSearchResults.map((mf) => (
                                <li key={mf.ticker_symbol} onClick={() => {
                                    setValue('mf_name', mf.name);
                                    setValue('mf_ticker_symbol', mf.ticker_symbol);
                                    setMfSearchQuery('');
                                }}>
                                    {mf.name}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            );
        } else if (assetType === 'Fixed Deposit') {
            return (
                <>
                    <div className="form-group">
                        <label htmlFor="fd_name" className="form-label">Institution Name</label>
                        <input id="fd_name" {...register('fd_name', { required: true })} className="form-input" />
                    </div>
                    <div className="form-group">
                        <label htmlFor="fd_account_number" className="form-label">FD Account Number</label>
                        <input id="fd_account_number" {...register('fd_account_number')} className="form-input" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="form-group">
                            <label htmlFor="fd_principal_amount" className="form-label">Principal Amount</label>
                            <input id="fd_principal_amount" type="number" {...register('fd_principal_amount', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="fd_interest_rate" className="form-label">Interest Rate (%)</label>
                            <input id="fd_interest_rate" type="number" step="0.01" {...register('fd_interest_rate', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                    </div>
                     <div className="grid grid-cols-2 gap-4">
                        <div className="form-group">
                            <label htmlFor="fd_start_date" className="form-label">Start Date</label>
                            <input id="fd_start_date" type="date" {...register('fd_start_date', { required: true })} className="form-input" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="fd_maturity_date" className="form-label">Maturity Date</label>
                            <input id="fd_maturity_date" type="date" {...register('fd_maturity_date', { required: true })} className="form-input" />
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="form-group">
                            <label htmlFor="fd_compounding_frequency" className="form-label">Compounding</label>
                            <select id="fd_compounding_frequency" {...register('fd_compounding_frequency')} className="form-input">
                                <option>Annually</option>
                                <option>Semi-Annually</option>
                                <option>Quarterly</option>
                                <option>Monthly</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="fd_interest_payout" className="form-label">Interest Payout</label>
                            <select id="fd_interest_payout" {...register('fd_interest_payout')} className="form-input">
                                <option>Cumulative</option>
                                <option>Monthly</option>
                                <option>Quarterly</option>
                                <option>Semi-Annually</option>
                                <option>Annually</option>
                            </select>
                        </div>
                    </div>
                </>
            );
        } else { // Stock
            return (
                <div className="form-group">
                    <label htmlFor="asset_name" className="form-label">Asset</label>
                    <input
                        id="asset_name"
                        type="text"
                        {...register('name')}
                        className="form-input"
                        placeholder="Search for a stock..."
                        onChange={(e) => setSearchQuery(e.target.value)}
                        disabled={isEditMode}
                    />
                    {isSearchLoading && <div>Searching...</div>}
                    {searchResults && searchQuery && !isCreatingNewAsset && (
                        <ul className="autocomplete-results">
                            {searchResults.map((asset) => (
                                <li key={asset.id} onClick={() => {
                                    setValue('asset_id', asset.id);
                                    setValue('name', asset.name);
                                    setValue('ticker_symbol', asset.ticker_symbol);
                                    setSearchQuery('');
                                }}>
                                    {asset.name} ({asset.ticker_symbol})
                                </li>
                            ))}
                            <li onClick={() => setIsCreatingNewAsset(true)}>
                                Can't find it? Add a new asset.
                            </li>
                        </ul>
                    )}
                    {isCreatingNewAsset && (
                        <div className="mt-2 p-2 border rounded">
                            <h4 className="font-semibold">Create New Asset</h4>
                            <input {...register('new_asset_name')} placeholder="Asset Name" className="form-input mt-1" />
                            <input {...register('new_asset_ticker')} placeholder="Ticker Symbol" className="form-input mt-1" />
                        </div>
                    )}
                </div>
            );
        }
    };



    return (
        <div className="modal-overlay z-30" onClick={onClose}>
            <div role="dialog" className="modal-content max-w-2xl" onClick={(e) => e.stopPropagation()}>
                <h2 className="text-2xl font-bold mb-4">{isEditMode ? 'Edit' : 'Add'} Transaction</h2>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    {apiError && <div className="alert alert-error"><p>{apiError}</p></div>}

                    <div className="form-group">
                        <label htmlFor="asset_type" className="form-label">Asset Type</label>
                        <select id="asset_type" {...register('asset_type')} className="form-input" disabled={isEditMode}>
                            <option value="Stock">Stock</option>
                            <option value="Mutual Fund">Mutual Fund</option>
                            <option value="Fixed Deposit">Fixed Deposit</option>
                            <option value="PPF Account">PPF Account</option>
                        </select>
                    </div>

                    {renderAssetSelection()}

                    {assetType === 'PPF Account' && ppfAccount && (
                        <div className="grid grid-cols-2 gap-4">
                            <div className="form-group">
                                <label htmlFor="quantity" className="form-label">Contribution Amount</label>
                                <input id="quantity" type="number" step="any" {...register('quantity', { required: true, valueAsNumber: true })} className="form-input" />
                            </div>
                            <div className="form-group">
                                <label htmlFor="transaction_date" className="form-label">Date</label>
                                <input id="transaction_date" type="date" {...register('transaction_date', { required: true })} className="form-input" />
                            </div>
                        </div>
                    )}

                    {assetType !== 'PPF Account' && assetType !== 'Fixed Deposit' && (
                        <>
                            <div className="form-group">
                                <label className="form-label">Transaction Type</label>
                                <div className="flex items-center space-x-4">
                                    <label className="flex items-center">
                                        <input type="radio" {...register('transaction_type')} value="BUY" className="form-radio" defaultChecked />
                                        <span className="ml-2">Buy</span>
                                    </label>
                                    <label className="flex items-center">
                                        <input type="radio" {...register('transaction_type')} value="SELL" className="form-radio" />
                                        <span className="ml-2">Sell</span>
                                    </label>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="form-group">
                                    <label htmlFor="quantity" className="form-label">Quantity</label>
                                    <input id="quantity" type="number" step="any" {...register('quantity', { required: true, valueAsNumber: true })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="price_per_unit" className="form-label">Price per Unit</label>
                                    <input id="price_per_unit" type="number" step="any" {...register('price_per_unit', { required: true, valueAsNumber: true })} className="form-input" />
                                </div>
                            </div>
                             <div className="grid grid-cols-2 gap-4">
                                <div className="form-group">
                                    <label htmlFor="transaction_date" className="form-label">Date</label>
                                    <input id="transaction_date" type="date" {...register('transaction_date', { required: true })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="fees" className="form-label">Fees (Optional)</label>
                                    <input id="fees" type="number" step="any" {...register('fees', { valueAsNumber: true })} className="form-input" />
                                </div>
                            </div>
                        </>
                    )}

                    <div className="flex justify-end space-x-4 pt-4">
                        <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                        <button type="submit" className="btn btn-primary" disabled={createTransactionMutation.isPending || updateTransactionMutation.isPending || createFixedDepositMutation.isPending}>
                            {isEditMode ? 'Save Changes' : 'Save'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default TransactionFormModal;
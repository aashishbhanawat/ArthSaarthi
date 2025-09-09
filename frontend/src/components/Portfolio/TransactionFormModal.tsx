import React, { useState, useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useCreateTransaction, useUpdateTransaction, useCreateFixedDeposit } from '../../hooks/usePortfolios';
import { useCreateRecurringDeposit } from '../../hooks/useRecurringDeposits';
import { useCreateAsset, useMfSearch } from '../../hooks/useAssets';
import { lookupAsset } from '../../services/portfolioApi';
import { Asset, MutualFundSearchResult } from '../../types/asset';
import { Transaction, TransactionCreate, TransactionUpdate } from '../../types/portfolio';
import Select from 'react-select';

interface TransactionFormModalProps {
    portfolioId: string;
    onClose: () => void;
    isOpen: boolean;
    transactionToEdit?: Transaction;
}

// Define the shape of our form data
type TransactionFormInputs = {
    asset_type: 'Stock' | 'Mutual Fund' | 'Fixed Deposit' | 'Recurring Deposit' | 'PPF Account';
    transaction_type: 'BUY' | 'SELL' | 'CONTRIBUTION';
    quantity: number;
    price_per_unit: number;
    transaction_date: string; // from date input
    fees?: number;
    // FD-specific fields
    institutionName?: string;
    accountNumber?: string;
    principalAmount?: number;
    interestRate?: number;
    startDate?: string;
    maturityDate?: string;
    compounding_frequency?: 'Annually' | 'Semi-Annually' | 'Quarterly' | 'Monthly';
    interest_payout?: 'Cumulative' | 'Monthly' | 'Quarterly' | 'Semi-Annually' | 'Annually';
    // RD-specific fields
    rdName?: string;
    rdAccountNumber?: string;
    monthlyInstallment?: number;
    rdInterestRate?: number;
    rdStartDate?: string;
    tenureMonths?: number;
    // PPF-specific fields
    ppfInstitutionName?: string;
    ppfAccountNumber?: string;
    ppfOpeningDate?: string;
};

const TransactionFormModal: React.FC<TransactionFormModalProps> = ({ portfolioId, onClose, isOpen, transactionToEdit }) => {
    const isEditMode = !!transactionToEdit;
    const { register, handleSubmit, formState: { errors }, reset, control } = useForm<TransactionFormInputs>({
        defaultValues: { asset_type: 'Stock' }
    });

    const createTransactionMutation = useCreateTransaction();
    const updateTransactionMutation = useUpdateTransaction();
    const createAssetMutation = useCreateAsset();
    const createFixedDepositMutation = useCreateFixedDeposit();
    const createRecurringDepositMutation = useCreateRecurringDeposit();

    const [apiError, setApiError] = useState<string | null>(null);

    // Stock search state
    const [inputValue, setInputValue] = useState('');
    const [searchTerm, setSearchTerm] = useState(''); // Debounced value
    const [searchResults, setSearchResults] = useState<Asset[]>([]);
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [isSearching, setIsSearching] = useState(false);

    // Watch the asset_type field to conditionally render inputs
    const assetType = useWatch({ control, name: 'asset_type' });

    // --- Mutual Fund Search State & Hooks ---
    const [mfSearchInput, setMfSearchInput] = useState('');
    const { data: mfSearchResults, isLoading: isMfSearching } = useMfSearch(mfSearchInput);
    const [selectedMf, setSelectedMf] = useState<MutualFundSearchResult | null>(null);

    useEffect(() => {
        if (isEditMode && transactionToEdit) {
            // Format date for input[type=date] which expects 'YYYY-MM-DD'
            const formattedDate = new Date(transactionToEdit.transaction_date).toISOString().split('T')[0];

            reset({
                transaction_type: transactionToEdit.transaction_type,
                asset_type: transactionToEdit.asset.asset_type === 'Mutual Fund' ? 'Mutual Fund' : 'Stock',
                quantity: Number(transactionToEdit.quantity),
                price_per_unit: Number(transactionToEdit.price_per_unit),
                transaction_date: formattedDate,
                fees: Number(transactionToEdit.fees),
            });
            setSelectedAsset(transactionToEdit.asset);
            setInputValue(transactionToEdit.asset.name);
            if (transactionToEdit.asset.asset_type === 'Mutual Fund') {
                setSelectedMf({ name: transactionToEdit.asset.name, ticker_symbol: transactionToEdit.asset.ticker_symbol, asset_type: 'Mutual Fund' });
            }
        }
    }, [isEditMode, transactionToEdit, reset]);

    // Debounce search term
    useEffect(() => {
        const handler = setTimeout(() => {
            setSearchTerm(inputValue);
        }, 300);

        return () => {
            clearTimeout(handler);
        };
    }, [inputValue]);

    useEffect(() => {
        if (searchTerm.length < 2 || selectedAsset) { // Use debounced term
            setSearchResults([]);
            return;
        }

        setIsSearching(true);
        lookupAsset(searchTerm)
            .then(data => setSearchResults(data))
            .catch(() => setSearchResults([]))
            .finally(() => setIsSearching(false));
    }, [searchTerm, selectedAsset]);

    const handleSelectAsset = (asset: Asset) => {
        setSelectedAsset(asset);
        setInputValue(asset.name);
        setSearchResults([]);
    };

    const handleClearSelectedAsset = () => {
        setSelectedAsset(null);
        setInputValue('');
    };

    const handleSelectMf = (mf: MutualFundSearchResult | null) => {
        setSelectedMf(mf);
    };

    const onSubmit = (data: TransactionFormInputs) => {
        const mutationOptions = {
            onSuccess: () => onClose(),
            onError: (error: Error & { response?: { data?: { detail?: string | { msg: string }[] } } }) => {
                const defaultMessage = isEditMode
                    ? 'An unexpected error occurred while updating the transaction'
                    : 'An unexpected error occurred while adding the transaction';

                let errorMessage = defaultMessage;
                const detail = error.response?.data?.detail;

                if (typeof detail === 'string') {
                    errorMessage = detail;
                } else if (Array.isArray(detail) && detail[0]?.msg) {
                    errorMessage = detail.map(d => d.msg).join(', ');
                } else if (error.message) {
                    errorMessage = error.message;
                }
                setApiError(errorMessage);
            }
        };

        if (assetType === 'Fixed Deposit') {
            createFixedDepositMutation.mutate({
                portfolioId: portfolioId,
                data: {
                    name: data.institutionName!,
                    account_number: data.accountNumber!,
                    principal_amount: data.principalAmount!,
                    interest_rate: data.interestRate!,
                    start_date: data.startDate!,
                    maturity_date: data.maturityDate!,
                    compounding_frequency: data.compounding_frequency || 'Annually',
                    interest_payout: data.interest_payout || 'Cumulative'
                }
            }, mutationOptions);
        } else if (assetType === 'Recurring Deposit') {
            createRecurringDepositMutation.mutate({
                portfolioId: portfolioId,
                data: {
                    name: data.rdName!,
                    account_number: data.rdAccountNumber!,
                    monthly_installment: data.monthlyInstallment!,
                    interest_rate: data.rdInterestRate!,
                    start_date: data.rdStartDate!,
                    tenure_months: data.tenureMonths!,
                }
            }, mutationOptions);
        } else if (assetType === 'PPF Account') {
            createAssetMutation.mutate({
                name: data.ppfInstitutionName!,
                account_number: data.ppfAccountNumber,
                opening_date: data.ppfOpeningDate!,
                asset_type: 'PPF',
                ticker_symbol: `PPF-${data.ppfAccountNumber || Date.now()}`,
                currency: 'INR',
            }, mutationOptions);
        } else {
            if (selectedAsset && selectedAsset.asset_type === 'PPF') {
                const payload: TransactionCreate = {
                    asset_id: selectedAsset.id,
                    transaction_type: 'CONTRIBUTION',
                    quantity: Number(data.quantity),
                    price_per_unit: 1, // For contributions, the "price" is 1 and quantity is the amount.
                    fees: 0,
                    transaction_date: new Date(data.transaction_date).toISOString(),
                    ticker_symbol: selectedAsset.ticker_symbol,
                };
                createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
                return; // Exit early
            }

            if (assetType === 'Stock' && !selectedAsset) {
                setApiError("Please select a stock.");
                return;
            }
            if (assetType === 'Mutual Fund' && !selectedMf) {
                setApiError("Please select a mutual fund.");
                return;
            }

            const { asset_type, ...transactionBaseData } = data;
            const commonPayload: Omit<TransactionUpdate, 'asset_id'> = {
                ...transactionBaseData,
                quantity: Number(data.quantity),
                price_per_unit: Number(data.price_per_unit),
                fees: data.fees ? Number(data.fees) : 0,
                transaction_date: new Date(data.transaction_date).toISOString(),
            };

            if (isEditMode && transactionToEdit) {
                const payload: TransactionUpdate = commonPayload;
                updateTransactionMutation.mutate(
                    { portfolioId, transactionId: transactionToEdit.id, data: payload },
                    mutationOptions
                );
            } else {
                let payload: TransactionCreate;
                if (asset_type === 'Stock' && selectedAsset) {
                    payload = {
                        ...commonPayload,
                        asset_id: selectedAsset.id,
                        ticker_symbol: selectedAsset.ticker_symbol,
                    };
                } else if (asset_type === 'Mutual Fund' && selectedMf) {
                    payload = { ...commonPayload, ticker_symbol: selectedMf.ticker_symbol, asset_type: 'Mutual Fund' };
                } else {
                    setApiError("An unexpected error occurred. Please select an asset.");
                    return;
                }
                createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
            }
        }
    };

    const handleCreateAsset = () => {
        setApiError(null);
        if (isEditMode) return;

        const payload = {
            ticker_symbol: inputValue.toUpperCase(),
            name: inputValue,
            asset_type: 'STOCK' as const,
            currency: 'INR',
        };

        createAssetMutation.mutate(payload, {
            onSuccess: (newAsset) => {
                handleSelectAsset(newAsset);
            },
            onError: (error: Error & { response?: { data?: { detail?: string | { msg: string }[] } } }) => {
                const defaultMessage = 'Failed to create asset.';
                let errorMessage = defaultMessage;
                const detail = error.response?.data?.detail;

                if (typeof detail === 'string') {
                    errorMessage = detail;
                } else if (Array.isArray(detail)) {
                    errorMessage = detail.map(d => d.msg).join(', ');
                }
                setApiError(errorMessage);
            }
        });
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay z-30" onClick={onClose} data-testid="transaction-form-modal-overlay">
            <div role="dialog" aria-modal="true" aria-labelledby="transaction-form-modal-title" className="modal-content overflow-visible w-11/12 md:w-3/4 lg:max-w-2xl p-6" onClick={e => e.stopPropagation()} data-testid="transaction-form-modal-content">
                <h2 id="transaction-form-modal-title" className="text-2xl font-bold mb-4">{isEditMode ? 'Edit' : 'Add'} Transaction</h2>
                <div className="max-h-[70vh] overflow-y-auto px-2 -mr-2">
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="form-group">
                                <label htmlFor="asset_type" className="form-label">Asset Type</label>
                                <select id="asset_type" {...register('asset_type')} className="form-input" disabled={isEditMode}>
                                    <option value="Stock">Stock</option>
                                    <option value="Mutual Fund">Mutual Fund</option>
                                    <option value="Fixed Deposit">Fixed Deposit</option>
                                    <option value="Recurring Deposit">Recurring Deposit</option>
                                    <option value="PPF Account">PPF Account</option>
                                </select>
                            </div>

                            {(assetType !== 'Fixed Deposit' && assetType !== 'Recurring Deposit' && assetType !== 'PPF Account') && (
                                <div className="form-group">
                                    <label htmlFor={assetType === 'Stock' ? 'asset-search' : 'mf-search-input'} className="form-label">Asset</label>
                                    {assetType === 'Stock' && (
                                    <div className="relative">
                                        <input
                                            type="text"
                                            id="asset-search"
                                            className="form-input"
                                            value={inputValue}
                                            onChange={(e) => {
                                                setApiError(null);
                                                if (selectedAsset) handleClearSelectedAsset();
                                                setInputValue(e.target.value);
                                            }}
                                            placeholder="Search by ticker or name..."
                                            autoComplete="off"
                                            disabled={isEditMode}
                                        />
                                        {!isEditMode && (
                                            <>
                                                {selectedAsset && (
                                                    <button type="button" onClick={handleClearSelectedAsset} className="absolute right-2 top-2 text-red-500 text-xl font-bold">
                                                        &times;
                                                    </button>
                                                )}
                                                {isSearching && <div className="absolute z-20 w-full bg-white border border-gray-300 rounded-md mt-1 p-2 shadow-lg">Searching...</div>}
                                                {!isSearching && searchResults.length > 0 && !selectedAsset && (
                                                    <ul className="absolute z-20 w-full bg-white border border-gray-300 rounded-md mt-1 max-h-40 overflow-y-auto shadow-lg">
                                                        {searchResults.map(asset => (
                                                            <li key={asset.id} onClick={() => handleSelectAsset(asset)} className="p-2 hover:bg-gray-100 cursor-pointer">
                                                                {asset.name} ({asset.ticker_symbol})
                                                            </li>
                                                        ))}
                                                    </ul>
                                                )}
                                                {!isSearching && searchResults.length === 0 && inputValue.length > 1 && !selectedAsset && (
                                                    <div className="absolute z-20 w-full bg-white border border-gray-300 rounded-md mt-1 p-2 shadow-lg">
                                                        <p className="text-sm text-gray-500 mb-2">No asset found. You can create it.</p>
                                                        <button type="button" onClick={handleCreateAsset} className="btn btn-secondary btn-sm w-full" disabled={createAssetMutation.isPending}>
                                                            {createAssetMutation.isPending ? 'Creating...' : `Create Asset "${inputValue.toUpperCase()}"`}
                                                        </button>
                                                    </div>
                                                )}
                                            </>
                                        )}
                                    </div>
                                )}
                                {assetType === 'Mutual Fund' && (
                                    <Select<MutualFundSearchResult>
                                        inputId="mf-search-input"
                                        value={selectedMf}
                                        onChange={(option) => handleSelectMf(option)}
                                        onInputChange={(value) => setMfSearchInput(value)}
                                        options={mfSearchResults}
                                        isLoading={isMfSearching}
                                        getOptionLabel={(option) => option.name}
                                        getOptionValue={(option) => option.ticker_symbol}
                                        isClearable
                                        isDisabled={isEditMode}
                                        placeholder="Search by fund name or scheme code..."
                                        noOptionsMessage={({ inputValue }) =>
                                            inputValue.length < 2
                                                ? 'Type at least 2 characters to search'
                                                : 'No funds found'
                                        }
                                        styles={{
                                            control: (base) => ({
                                                ...base,
                                                backgroundColor: '#fff',
                                                borderColor: '#d1d5db',
                                                minHeight: '42px',
                                            }),
                                            menu: (base) => ({
                                                ...base,
                                                zIndex: 30,
                                            }),
                                        }}
                                    />
                                )}
                                </div>
                            )}
                        </div>

                        {/* Logic to show the correct form based on selection */}
                        {(() => {
                            if (selectedAsset?.asset_type === 'PPF') {
                                // Form for adding a contribution to an existing PPF asset
                                return (
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="form-group">
                                            <label htmlFor="transaction_type" className="form-label">Type</label>
                                            <input id="transaction_type" type="text" value="Contribution" className="form-input bg-gray-100" disabled />
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="quantity" className="form-label">Contribution Amount</label>
                                            <input id="quantity" type="number" step="any" {...register('quantity', { required: "Amount is required", valueAsNumber: true, min: { value: 0.01, message: "Must be positive" } })} className="form-input" />
                                            {errors.quantity && <p className="text-red-500 text-xs italic">{errors.quantity.message}</p>}
                                        </div>
                                        <div className="form-group col-span-2">
                                            <label htmlFor="transaction_date" className="form-label">Date</label>
                                            <input id="transaction_date" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                            {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                        </div>
                                    </div>
                                );
                            } else if (assetType !== 'Fixed Deposit' && assetType !== 'Recurring Deposit' && assetType !== 'PPF Account') {
                                // Standard transaction form for Stocks and MF
                                return (
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="form-group">
                                            <label htmlFor="transaction_type" className="form-label">Type</label>
                                            <select id="transaction_type" {...register('transaction_type')} className="form-input">
                                                <option value="BUY">Buy</option>
                                                <option value="SELL">Sell</option>
                                            </select>
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="quantity" className="form-label">Quantity</label>
                                            <input id="quantity" type="number" step="any" {...register('quantity', { required: "Quantity is required", valueAsNumber: true, min: { value: 0.000001, message: "Must be positive" } })} className="form-input" />
                                            {errors.quantity && <p className="text-red-500 text-xs italic">{errors.quantity.message}</p>}
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="price_per_unit" className="form-label">Price per Unit</label>
                                            <input id="price_per_unit" type="number" step="any" {...register('price_per_unit', { required: "Price is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                            {errors.price_per_unit && <p className="text-red-500 text-xs italic">{errors.price_per_unit.message}</p>}
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="transaction_date" className="form-label">Date</label>
                                            <input id="transaction_date" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                            {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                        </div>
                                        <div className="form-group col-span-2">
                                            <label htmlFor="fees" className="form-label">Fees (optional)</label>
                                            <input id="fees" type="number" step="any" {...register('fees', { valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                            {errors.fees && <p className="text-red-500 text-xs italic">{errors.fees.message}</p>}
                                        </div>
                                    </div>
                                );
                            }
                            return null; // Render nothing if it's a deposit or new PPF account form
                        })()}

                        {assetType === 'Fixed Deposit' && (
                            <div className="grid grid-cols-2 gap-4">
                                <div className="form-group">
                                    <label htmlFor="institutionName" className="form-label">Institution Name</label>
                                    <input id="institutionName" type="text" {...register('institutionName', { required: "Institution name is required" })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="accountNumber" className="form-label">FD Account Number</label>
                                    <input id="accountNumber" type="text" {...register('accountNumber')} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="principalAmount" className="form-label">Principal Amount</label>
                                    <input id="principalAmount" type="number" step="any" {...register('principalAmount', { required: "Principal is required", valueAsNumber: true, min: { value: 0.01, message: "Must be positive" } })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="interestRate" className="form-label">Interest Rate (%)</label>
                                    <input id="interestRate" type="number" step="any" {...register('interestRate', { required: "Interest rate is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="startDate" className="form-label">Start Date</label>
                                    <input id="startDate" type="date" {...register('startDate', { required: "Start date is required" })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="maturityDate" className="form-label">Maturity Date</label>
                                    <input id="maturityDate" type="date" {...register('maturityDate', { required: "Maturity date is required" })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="compounding_frequency" className="form-label">Compounding</label>
                                    <select id="compounding_frequency" {...register('compounding_frequency')} className="form-input">
                                        <option value="Annually">Annually</option>
                                        <option value="Semi-Annually">Semi-Annually</option>
                                        <option value="Quarterly">Quarterly</option>
                                        <option value="Monthly">Monthly</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label htmlFor="interest_payout" className="form-label">Interest Payout</label>
                                    <select id="interest_payout" {...register('interest_payout')} className="form-input">
                                        <option value="Cumulative">Cumulative (at maturity)</option>
                                        <option value="Payout">Periodic Payout</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {assetType === 'Recurring Deposit' && (
                            <div className="grid grid-cols-2 gap-4">
                                <div className="form-group">
                                    <label htmlFor="rdName" className="form-label">Institution Name</label>
                                    <input id="rdName" type="text" {...register('rdName', { required: "Institution name is required" })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="rdAccountNumber" className="form-label">RD Account Number</label>
                                    <input id="rdAccountNumber" type="text" {...register('rdAccountNumber')} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="monthlyInstallment" className="form-label">Monthly Installment</label>
                                    <input id="monthlyInstallment" type="number" step="any" {...register('monthlyInstallment', { required: "Monthly installment is required", valueAsNumber: true, min: { value: 0.01, message: "Must be positive" } })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="rdInterestRate" className="form-label">Interest Rate (%)</label>
                                    <input id="rdInterestRate" type="number" step="any" {...register('rdInterestRate', { required: "Interest rate is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="rdStartDate" className="form-label">Start Date</label>
                                    <input id="rdStartDate" type="date" {...register('rdStartDate', { required: "Start date is required" })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="tenureMonths" className="form-label">Tenure (in months)</label>
                                    <input id="tenureMonths" type="number" {...register('tenureMonths', { required: "Tenure is required", valueAsNumber: true, min: { value: 1, message: "Must be at least 1" } })} className="form-input" />
                                </div>
                            </div>
                        )}

                        {assetType === 'PPF Account' && (
                            <div className="grid grid-cols-2 gap-4">
                                <div className="form-group col-span-2">
                                    <label htmlFor="ppfInstitutionName" className="form-label">Institution Name (e.g., SBI, HDFC)</label>
                                    <input id="ppfInstitutionName" type="text" {...register('ppfInstitutionName', { required: "Institution name is required" })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="ppfAccountNumber" className="form-label">Account Number (optional)</label>
                                    <input id="ppfAccountNumber" type="text" {...register('ppfAccountNumber')} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="ppfOpeningDate" className="form-label">Opening Date</label>
                                    <input id="ppfOpeningDate" type="date" {...register('ppfOpeningDate', { required: "Opening date is required" })} className="form-input" />
                                </div>
                            </div>
                        )}

                        {apiError && (
                            <div className="alert alert-error mt-2">
                                <p>{apiError}</p>
                            </div>
                        )}

                        <div className="flex justify-end space-x-4 pt-4">
                            <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={
                                    (isEditMode && updateTransactionMutation.isPending) ||
                                    (!isEditMode && createTransactionMutation.isPending) ||
                                    (!isEditMode && assetType === 'Stock' && !selectedAsset) ||
                                    (!isEditMode && assetType === 'Mutual Fund' && !selectedMf)}
                            >
                                {isEditMode
                                    ? (updateTransactionMutation.isPending ? 'Saving...' : 'Save Changes')
                                    : (createTransactionMutation.isPending ? 'Saving...' : 'Save Transaction')
                                }
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default TransactionFormModal;
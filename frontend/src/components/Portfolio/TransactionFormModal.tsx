import React, { useState, useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useQueryClient } from '@tanstack/react-query';
import { useCreateTransaction, useUpdateTransaction, useCreateFixedDeposit, useCreatePpfAccount, useCreateBond } from '../../hooks/usePortfolios';
import { useCreateRecurringDeposit } from '../../hooks/useRecurringDeposits';
import { useCreateAsset, useMfSearch, useAssetsByType } from '../../hooks/useAssets';
import { lookupAsset } from '../../services/portfolioApi';
import { BondCreate, BondType } from '../../types/bond';
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
    asset_type: 'Stock' | 'Mutual Fund' | 'Fixed Deposit' | 'Recurring Deposit' | 'PPF Account' | 'Bond';
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
    compounding_frequency?: 'Annually' | 'Semi-Annually' | 'Quarterly' | 'Monthly'; // FD
    interest_payout?: 'Cumulative' | 'Monthly' | 'Quarterly' | 'Semi-Annually' | 'Annually'; // FD
    // RD-specific fields
    rdName?: string;
    rdAccountNumber?: string;
    monthlyInstallment?: number;
    rdInterestRate?: number;
    rdStartDate?: string;
    tenureMonths?: number;
    // PPF-specific fields (reusing generic fields for creation/contribution)
    contributionAmount?: number;
    contributionDate?: string;
    openingDate?: string;
    // Bond-specific fields
    bondType?: BondType;
    isin?: string;
    couponRate?: number;
    faceValue?: number;
    bondMaturityDate?: string;
};

const TransactionFormModal: React.FC<TransactionFormModalProps> = ({ portfolioId, onClose, isOpen, transactionToEdit }) => {
    const isEditMode = !!transactionToEdit;
  const { register, handleSubmit, formState: { errors }, reset, control, setValue } = useForm<TransactionFormInputs>({
        defaultValues: { asset_type: 'Stock' }
    });

    const queryClient = useQueryClient();
    const createTransactionMutation = useCreateTransaction();
    const updateTransactionMutation = useUpdateTransaction();
    const createAssetMutation = useCreateAsset();
    const createFixedDepositMutation = useCreateFixedDeposit();
    const createRecurringDepositMutation = useCreateRecurringDeposit();
    const createBondMutation = useCreateBond();
    const createPpfAccountMutation = useCreatePpfAccount();
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

    // --- PPF Account State & Hooks ---
    const { data: ppfAssets, isLoading: isLoadingPpfAssets } = useAssetsByType(
        portfolioId,
        'PPF',
        {
            enabled: assetType === 'PPF Account',
        }
    );
    const existingPpfAsset = ppfAssets?.[0];


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

        const assetTypeFilter = assetType === 'Bond' ? 'BOND' : (assetType === 'Stock' ? 'STOCK' : undefined);
        setIsSearching(true);
        lookupAsset(searchTerm, assetTypeFilter)
            .then(data => setSearchResults(data))
            .catch(() => setSearchResults([]))
            .finally(() => setIsSearching(false));
    }, [searchTerm, selectedAsset, assetType]);

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

  useEffect(() => {
        if (selectedAsset && assetType === 'Bond') {
            // Populate the bond-specific fields when a bond asset is selected
            setValue('bondType', selectedAsset.bond?.bond_type || '', { shouldValidate: true });
            setValue('isin', selectedAsset.isin || '', { shouldValidate: true });
            setValue('couponRate', selectedAsset.bond?.coupon_rate || '', { shouldValidate: true });
            setValue('faceValue', selectedAsset.bond?.face_value || '', { shouldValidate: true });
            setValue('bondMaturityDate', selectedAsset.bond?.maturity_date ? new Date(selectedAsset.bond.maturity_date).toISOString().split('T')[0] : '', { shouldValidate: true });
        }
    }, [selectedAsset, assetType, setValue]);


    const handleCreateAsset = () => {
        if (inputValue) {
            setSelectedAsset({ name: inputValue, ticker_symbol: inputValue.toUpperCase() } as Asset);
        }
    };

    const onSubmit = (data: TransactionFormInputs) => {
        // Defensively coalesce NaN to 0. This can happen if the fees input is left blank.
        if (isNaN(data.fees as number)) {
            data.fees = 0;
        }

        const mutationOptions = {
            onSuccess: () => {
                // Always invalidate portfolio queries on success to refetch holdings, summary, etc.
                queryClient.invalidateQueries({ queryKey: ['portfolio', portfolioId] });
                onClose();
            },
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

        if (assetType === 'PPF Account') {
            if (existingPpfAsset) {
                // Add a new contribution to an existing PPF account
                const payload: TransactionCreate = {
                    asset_id: existingPpfAsset.id,
                    transaction_type: 'CONTRIBUTION',
                    quantity: data.contributionAmount!,
                    price_per_unit: 1,
                    transaction_date: new Date(data.contributionDate!).toISOString(),
                    asset_type: 'PPF', // For smart recalculation trigger
                };
                createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
            } else {
                // Create a new PPF account and the first contribution
                createPpfAccountMutation.mutate({
                    portfolioId,
                    data: {
                        institution_name: data.institutionName!,
                        account_number: data.accountNumber,
                        opening_date: data.openingDate!,
                        amount: data.contributionAmount!,
                        contribution_date: data.contributionDate!,
                    }
                }, mutationOptions);
            }
        } else if (assetType === 'Fixed Deposit') {
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
        } else if (assetType === 'Bond') {
            if (!selectedAsset) {
                setApiError("Please select or create a bond asset.");
                return;
            }

            const createBondAndTransaction = (assetId: string) => {
                const bondData: BondCreate = {
                    bond_type: data.bondType!,
                    coupon_rate: data.couponRate!,
                    face_value: data.faceValue!,
                    maturity_date: data.bondMaturityDate!,
                    isin: data.isin,
                    payment_frequency: null,
                    first_payment_date: null,
                };
                const transactionData: TransactionCreate = { asset_id: assetId, transaction_type: 'BUY', quantity: data.quantity, price_per_unit: data.price_per_unit, transaction_date: new Date(data.transaction_date).toISOString(), fees: data.fees || 0 };
                createBondMutation.mutate({ portfolioId, bondData, transactionData }, mutationOptions);
            };

            if (selectedAsset.id) {
                createBondAndTransaction(selectedAsset.id);
            } else {
                // Asset needs to be created first
                createAssetMutation.mutate(
                    { ticker_symbol: selectedAsset.ticker_symbol, name: selectedAsset.name, asset_type: 'BOND', currency: 'INR' },
                    {
                        onSuccess: (newAsset) => createBondAndTransaction(newAsset.id),
                        onError: () => setApiError(`Failed to create asset "${selectedAsset.name}".`),
                    }
                );
            }
        } else {
            // Handle Stock and Mutual Fund
            if (isEditMode && transactionToEdit) {
                const payload: TransactionUpdate = {
                    quantity: data.quantity,
                    price_per_unit: data.price_per_unit,
                    transaction_date: new Date(data.transaction_date).toISOString(),
                    fees: data.fees || 0,
                };
                updateTransactionMutation.mutate({ portfolioId, transactionId: transactionToEdit.id, data: payload }, mutationOptions);
            } else {
                const commonPayload = {
                    transaction_type: data.transaction_type,
                    quantity: data.quantity,
                    price_per_unit: data.price_per_unit,
                    transaction_date: new Date(data.transaction_date).toISOString(),
                    fees: data.fees || 0,
                };

                const createTransactionForAsset = (assetId: string, ticker: string) => {
                    const payload: TransactionCreate = { ...commonPayload, asset_id: assetId, ticker_symbol: ticker };
                    createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
                };

                if (assetType === 'Stock' && selectedAsset) {
                    if (selectedAsset.id) {
                        // Asset already exists
                        createTransactionForAsset(selectedAsset.id, selectedAsset.ticker_symbol);
                    } else {
                        // Asset needs to be created first
                        createAssetMutation.mutate(
                            {
                                ticker_symbol: selectedAsset.ticker_symbol,
                                name: selectedAsset.name,
                                asset_type: 'STOCK',
                                currency: 'INR',
                            },
                            {
                                onSuccess: (newAsset) => createTransactionForAsset(newAsset.id, newAsset.ticker_symbol),
                                onError: () => setApiError(`Failed to create asset "${selectedAsset.name}".`),
                            }
                        );
                    }
                } else if (assetType === 'Mutual Fund' && selectedMf) {
                    const payload = { ...commonPayload, ticker_symbol: selectedMf.ticker_symbol, asset_type: 'Mutual Fund' as const };
                    createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
                } else {
                    setApiError("Please select an asset.");
                    return;
                }
            }
        }
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
                                    <option value="Bond">Bond</option>
                                </select>
                            </div>

                            {(assetType === 'Stock' || assetType === 'Mutual Fund' || assetType === 'Bond') && (
                                <div className="form-group">
                                    {assetType === 'Stock' && (
                                        <>
                                            <label htmlFor="asset-search" className="form-label">Asset</label>
                                            <div className="relative" data-testid="stock-asset-search">
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
                                        </>
                                    )}
                                    {assetType === 'Mutual Fund' && (
                                        <>
                                            <label htmlFor="mf-search-input" className="form-label">Asset</label>
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
                                        </>
                                    )}
                                    {assetType === 'Bond' && (
                                        <>
                                            <label htmlFor="bond-asset-search" className="form-label">Bond Asset</label>
                                            <div className="relative" data-testid="bond-asset-search">
                                                <input
                                                    type="text"
                                                    id="bond-asset-search"
                                                    className="form-input"
                                                    value={inputValue}
                                                    onChange={(e) => {
                                                        setApiError(null);
                                                        if (selectedAsset) handleClearSelectedAsset();
                                                        setInputValue(e.target.value);
                                                    }}
                                                    placeholder="Search by ISIN or name..."
                                                    autoComplete="off"
                                                    disabled={isEditMode}
                                                />
                                                {!isEditMode && (
                                                    <>
                                                        {selectedAsset && (
                                                            <button type="button" onClick={handleClearSelectedAsset} className="absolute right-2 top-2 text-red-500 text-xl font-bold">
                                                                
                                                            </button>
                                                        )}
                                                        {isSearching && <div className="absolute z-20 w-full bg-white border border-gray-300 rounded-md mt-1 p-2 shadow-lg">Searching...</div>}
                                                        {!isSearching && searchResults.length > 0 && !selectedAsset && (
                                                            <ul className="absolute z-20 w-full bg-white border border-gray-300 rounded-md mt-1 max-h-40 overflow-y-auto shadow-lg" data-testid="bond-search-results">
                                                                {searchResults.map(asset => (
                                                                    <li key={asset.id} onClick={() => handleSelectAsset(asset)} className="p-2 hover:bg-gray-100 cursor-pointer">
                                                                        {asset.name} ({asset.ticker_symbol})
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        )}
                                                        {!isSearching && searchResults.length > 0 && searchResults.filter(a => a.asset_type === 'BOND').length === 0 && !selectedAsset && assetType === 'Bond' && (
                                                            <div className="absolute z-20 w-full bg-white border border-gray-300 rounded-md mt-1 p-2 shadow-lg" data-testid="no-bond-results">
                                                                <p className="text-sm text-gray-500">No bond assets found for "{inputValue}" .</p>
                                                            </div>
                                                        )}
                                                        {!isSearching && searchResults.length === 0 && inputValue.length > 1 && !selectedAsset && (
                                                            <div className="absolute z-20 w-full bg-white border border-gray-300 rounded-md mt-1 p-2 shadow-lg" data-testid="create-new-asset-section">
                                                                <p className="text-sm text-gray-500 mb-2">No {assetType === 'Stock' ? 'stock' : 'bond'} found. You can create it.</p>
                                                                <button type="button" onClick={handleCreateAsset} className="btn btn-secondary btn-sm w-full" disabled={createAssetMutation.isPending}>
                                                                    {createAssetMutation.isPending ? 'Creating...' : `Create ${assetType} "${inputValue.toUpperCase()}"`}
                                                                </button>
                                                            </div>
                                                        )}
                                                    </>
                                                )}
                                            </div>
                                        </>
                                    )}
                                    
                                </div>
                            )}
                        </div>

                        {(assetType === 'PPF Account') && (
                            isLoadingPpfAssets ? <p>Loading PPF details...</p> : (
                                existingPpfAsset ? (
                                    <div>
                                        <div className="p-4 border rounded-md bg-gray-50 mb-4">
                                            <h3 className="font-semibold text-lg text-gray-800">Existing PPF Account</h3>
                                            <p className="text-sm text-gray-600">Institution: {existingPpfAsset.name}</p>
                                            <p className="text-sm text-gray-600">Account #: {existingPpfAsset.account_number}</p>
                                        </div>
                                        <h3 className="font-semibold text-lg text-gray-800 mb-2">Add New Contribution</h3>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="form-group">
                                                <label htmlFor="contributionAmount" className="form-label">Contribution Amount (₹)</label>
                                                <input id="contributionAmount" type="number" step="any" {...register('contributionAmount', { required: true, valueAsNumber: true })} className="form-input" />
                                            </div>
                                            <div className="form-group">
                                                <label htmlFor="contributionDate" className="form-label">Contribution Date</label>
                                                <input id="contributionDate" type="date" {...register('contributionDate', { required: true })} className="form-input" />
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div>
                                        <h3 className="font-semibold text-lg text-gray-800 mb-2">Create Your PPF Account</h3>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="form-group col-span-2">
                                                <label htmlFor="institutionName" className="form-label">Institution Name (e.g., SBI, HDFC)</label>
                                                <input id="institutionName" type="text" {...register('institutionName', { required: true })} className="form-input" />
                                            </div>
                                            <div className="form-group">
                                                <label htmlFor="accountNumber" className="form-label">Account Number (Optional)</label>
                                                <input id="accountNumber" type="text" {...register('accountNumber')} className="form-input" />
                                            </div>
                                            <div className="form-group">
                                                <label htmlFor="openingDate" className="form-label">Opening Date</label>
                                                <input id="openingDate" type="date" {...register('openingDate', { required: true })} className="form-input" />
                                            </div>
                                        </div>
                                        <h3 className="font-semibold text-lg text-gray-800 mt-4 mb-2">Add First Contribution</h3>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="form-group">
                                                <label htmlFor="contributionAmount" className="form-label">Contribution Amount (₹)</label>
                                                <input id="contributionAmount" type="number" step="any" {...register('contributionAmount', { required: true, valueAsNumber: true })} className="form-input" />
                                            </div>
                                            <div className="form-group">
                                                <label htmlFor="contributionDate" className="form-label">Contribution Date</label>
                                                <input id="contributionDate" type="date" {...register('contributionDate', { required: true })} className="form-input" />
                                            </div>
                                        </div>
                                    </div>
                                )
                            )
                        )}

                        {assetType === 'Bond' && (
                            <div className="grid grid-cols-2 gap-4">
                                <div className="form-group">
                                    <label htmlFor="bondType" className="form-label">Bond Type</label>
                                    <select id="bondType" {...register('bondType', { required: true })} className="form-input">
                                        {Object.values(BondType).map(type => <option key={type} value={type}>{type}</option>)}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label htmlFor="isin" className="form-label">ISIN (Optional)</label>
                                    <input id="isin" type="text" {...register('isin')} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="couponRate" className="form-label">Coupon Rate (%)</label>
                                    <input id="couponRate" type="number" step="any" {...register('couponRate', { required: true, valueAsNumber: true })} className="form-input" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="faceValue" className="form-label">Face Value</label>
                                    <input id="faceValue" type="number" step="any" {...register('faceValue', { required: true, valueAsNumber: true })} className="form-input" />
                                </div>
                                <div className="form-group col-span-2">
                                    <label htmlFor="bondMaturityDate" className="form-label">Maturity Date</label>
                                    <input id="bondMaturityDate" type="date" {...register('bondMaturityDate', { required: true })} className="form-input" />
                                </div>
                            </div>
                        )}

                        {(assetType === 'Stock' || assetType === 'Mutual Fund' || assetType === 'Bond') && (
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
                        )}

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
                                        <option value="Cumulative">Cumulative (Re-invested)</option>
                                        <option value="Payout">Payout (Periodic)</option>
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
                                    (!isEditMode && (createTransactionMutation.isPending || createPpfAccountMutation.isPending || createBondMutation.isPending)) ||
                                    (!isEditMode && assetType === 'Stock' && !selectedAsset) ||
                                    (!isEditMode && assetType === 'Mutual Fund' && !selectedMf)}
                            >
                                {isEditMode 
                                    ? (updateTransactionMutation.isPending ? 'Saving...' : 'Save Changes')
                                    : (createTransactionMutation.isPending || createPpfAccountMutation.isPending || createBondMutation.isPending ? 'Saving...' : 'Save Transaction')
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
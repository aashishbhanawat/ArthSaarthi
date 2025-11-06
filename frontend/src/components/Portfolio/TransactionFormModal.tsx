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
    transaction_type: 'BUY' | 'SELL' | 'DIVIDEND' | 'CONTRIBUTION' | 'Corporate Action' | 'COUPON';
    action_type: 'DIVIDEND' | 'SPLIT' | 'BONUS';
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
    // Corporate Action fields
    dividendAmount?: number;
    mfDividendAmount?: number;
    isReinvested?: boolean;
    reinvestmentNav?: number;
    splitRatioNew?: number;
    splitRatioOld?: number;
    bonusRatioNew?: number;
    bonusRatioOld?: number;
    couponAmount?: number;
    assetId?: string;
};

const TransactionFormModal: React.FC<TransactionFormModalProps> = ({ portfolioId, onClose, isOpen, transactionToEdit }) => {
    const isEditMode = !!transactionToEdit;
    const { register, handleSubmit, formState: { errors }, reset, control, setValue } = useForm<TransactionFormInputs>({
        defaultValues: { asset_type: 'Stock', transaction_type: 'BUY', action_type: 'DIVIDEND', splitRatioNew: 2, splitRatioOld: 1, bonusRatioNew: 1, bonusRatioOld: 1 }
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

    // Watch fields to conditionally render inputs
    const assetType = useWatch({ control, name: 'asset_type' });
    const transactionType = useWatch({ control, name: 'transaction_type' });
    const actionType = useWatch({ control, name: 'action_type' });
    const isReinvested = useWatch({ control, name: 'isReinvested' });

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
                // More specific invalidations are handled by the hook itself.
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

        // --- Corporate Action Logic ---
        if (assetType === 'Stock' && transactionType === 'Corporate Action') {
            if (!selectedAsset || !selectedAsset.id) {
                setApiError("Please select a stock to apply the corporate action to.");
                return;
            }

            let payload: TransactionCreate;

            switch (data.action_type) {
                case 'DIVIDEND':
                    payload = {
                        asset_id: selectedAsset.id,
                        transaction_type: 'DIVIDEND',
                        quantity: data.dividendAmount!, // Repurposed for total cash amount
                        price_per_unit: 1, // Repurposed, set to 1
                        transaction_date: new Date(data.transaction_date).toISOString(),
                    };
                    break;
                case 'SPLIT':
                    payload = {
                        asset_id: selectedAsset.id,
                        transaction_type: 'SPLIT',
                        quantity: data.splitRatioNew!, // Repurposed for new part of ratio
                        price_per_unit: data.splitRatioOld!, // Repurposed for old part of ratio
                        transaction_date: new Date(data.transaction_date).toISOString(),
                    };
                    break;
                case 'BONUS':
                     payload = {
                        asset_id: selectedAsset.id,
                        transaction_type: 'BONUS',
                        quantity: data.bonusRatioNew!, // Repurposed for new shares received
                        price_per_unit: data.bonusRatioOld!, // Repurposed for old shares held
                        transaction_date: new Date(data.transaction_date).toISOString(),
                    };
                    break;
                default:
                    setApiError("Invalid corporate action type selected.");
                    return;
            }

            createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
            return; // Exit after handling corporate action
        }
        
        // --- Bond Coupon Logic ---
        if (assetType === 'Bond' && transactionType === 'COUPON') {
            if (!selectedAsset || !selectedAsset.id) {
                setApiError("Please select a bond to apply the coupon to.");
                return;
            }
            const payload: TransactionCreate = {
                asset_id: selectedAsset.id,
                transaction_type: 'COUPON',
                quantity: data.couponAmount!, // Repurposed for total cash amount
                price_per_unit: 1,
                transaction_date: new Date(data.transaction_date).toISOString(),
            };
            createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
            return;
        }

        // --- Mutual Fund Dividend Logic ---
        if (assetType === 'Mutual Fund' && data.transaction_type === 'DIVIDEND') {
            if (!selectedMf) {
                setApiError("Please select a mutual fund.");
                return;
            }

            let payload: TransactionCreate | TransactionCreate[];

            if (data.isReinvested) {
                // For reinvestment, create two transactions: one for the dividend income, one for the new units bought.
                const dividendTx: TransactionCreate = {
                    ticker_symbol: selectedMf.ticker_symbol,
                    asset_type: 'Mutual Fund',
                    transaction_type: 'DIVIDEND',
                    quantity: data.mfDividendAmount!,
                    price_per_unit: 1, // Price is 1 for dividend amount
                    transaction_date: new Date(data.transaction_date).toISOString(),
                };

                const reinvestedQuantity = data.mfDividendAmount! / data.reinvestmentNav!;
                const buyTx: TransactionCreate = {
                    ticker_symbol: selectedMf.ticker_symbol,
                    asset_type: 'Mutual Fund',
                    transaction_type: 'BUY',
                    quantity: reinvestedQuantity,
                    price_per_unit: data.reinvestmentNav!,
                    transaction_date: new Date(data.transaction_date).toISOString(),
                };
                payload = [dividendTx, buyTx];
            } else {
                // For simple cash dividend, create only one transaction.
                payload = { ticker_symbol: selectedMf.ticker_symbol, asset_type: 'Mutual Fund', transaction_type: 'DIVIDEND', quantity: data.mfDividendAmount!, price_per_unit: 1, transaction_date: new Date(data.transaction_date).toISOString() };
            }

            createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
            return;
        }

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
                
                // If the asset already exists and its bond details are complete (i.e., not a placeholder),
                // we just add a new transaction. Otherwise, we use the bond creation endpoint which
                // also handles updating (upserting) the bond details along with creating the first transaction.
                const isBondDetailComplete = selectedAsset.bond && selectedAsset.bond.maturity_date && selectedAsset.bond.maturity_date !== '1970-01-01';
                if (isBondDetailComplete) {
                     const payload: TransactionCreate = { ...transactionData, asset_id: selectedAsset.id, ticker_symbol: selectedAsset.ticker_symbol };
                     createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
                } else {
                    // This is for creating a new bond asset and its first transaction
                    createBondMutation.mutate({ portfolioId, bondData, transactionData }, mutationOptions);
                }
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
            // Handle Stock and Mutual Fund BUY/SELL
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

                        {/* Transaction Type Dropdown for Stocks */}
                        {assetType === 'Stock' && !isEditMode && (
                            <div className="form-group">
                                <label htmlFor="transaction_type" className="form-label">Transaction Type</label>
                                <select id="transaction_type" {...register('transaction_type')} className="form-input">
                                    <option value="BUY">Buy</option>
                                    <option value="SELL">Sell</option>
                                    <option value="Corporate Action">Corporate Action</option>
                                </select>
                            </div>
                        )}
                        {assetType === 'Bond' && !isEditMode && (
                            <div className="form-group">
                                <label htmlFor="transaction_type_bond" className="form-label">Type</label>
                                <select id="transaction_type_bond" {...register('transaction_type')} className="form-input">
                                    <option value="BUY">Buy</option>
                                    <option value="SELL">Sell</option>
                                    <option value="COUPON">Coupon</option>
                                </select>
                            </div>
                        )}

                        {/* Standard BUY/SELL Form */}
                        {((assetType === 'Stock' && transactionType !== 'Corporate Action') || (assetType === 'Mutual Fund' && transactionType !== 'DIVIDEND') || (assetType === 'Bond' && transactionType !== 'COUPON')) && (
                            <div className="space-y-4 p-4 border border-gray-200 rounded-md bg-gray-50/50">
                                {/* For MF, we need the buy/sell/dividend dropdown. For bonds, it's always buy. For stocks, it's handled above */}
                                {assetType === 'Mutual Fund' && !isEditMode && (
                                    <div className="form-group">
                                        <label htmlFor="transaction_type_mf" className="form-label">Type</label>
                                        <select id="transaction_type_mf" {...register('transaction_type')} className="form-input">
                                            <option value="BUY">Buy</option>
                                            <option value="SELL">Sell</option>
                                            <option value="DIVIDEND">Dividend</option>
                                        </select>
                                    </div>
                                )}
                                { (
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="form-group">
                                            <label htmlFor="quantity" className="form-label">Quantity</label>
                                            <input id="quantity" type="number" step="any" {...register('quantity', { required: transactionType !== 'Corporate Action', valueAsNumber: true, min: { value: 0.000001, message: "Must be positive" } })} className="form-input" />
                                            {errors.quantity && <p className="text-red-500 text-xs italic">{errors.quantity.message}</p>}
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="price_per_unit" className="form-label">Price per Unit</label>
                                            <input id="price_per_unit" type="number" step="any" {...register('price_per_unit', { required: transactionType !== 'Corporate Action', valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                            {errors.price_per_unit && <p className="text-red-500 text-xs italic">{errors.price_per_unit.message}</p>}
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="transaction_date_standard" className="form-label">Date</label>
                                            <input id="transaction_date_standard" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                            {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="fees" className="form-label">Fees (optional)</label>
                                            <input id="fees" type="number" step="any" {...register('fees', { valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                            {errors.fees && <p className="text-red-500 text-xs italic">{errors.fees.message}</p>}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        
                        {/* Standalone forms for MF Dividend and Bond Coupon */}
                        {assetType === 'Mutual Fund' && transactionType === 'DIVIDEND' && !isEditMode && (
                             <div className="space-y-4 p-4 border border-gray-200 rounded-md bg-gray-50/50">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="form-group">
                                        <label htmlFor="mfDividendAmount" className="form-label">Total Dividend Amount</label>
                                        <input id="mfDividendAmount" type="number" step="any" {...register('mfDividendAmount', { required: "Amount is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                        {errors.mfDividendAmount && <p className="text-red-500 text-xs italic">{errors.mfDividendAmount.message}</p>}
                                    </div>
                                    <div className="form-group">
                                        <label htmlFor="transaction_date_mf_dividend" className="form-label">Payment Date</label>
                                        <input id="transaction_date_mf_dividend" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                        {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                    </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <input id="isReinvested" type="checkbox" {...register('isReinvested')} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                                    <label htmlFor="isReinvested" className="text-sm text-gray-700">Reinvested?</label>
                                </div>
                                {isReinvested && (
                                    <div className="form-group">
                                        <label htmlFor="reinvestmentNav" className="form-label">NAV on Reinvestment Date</label>
                                        <input
                                            id="reinvestmentNav"
                                            type="number"
                                            step="any"
                                            {...register('reinvestmentNav', { required: "NAV is required for reinvestment", valueAsNumber: true, min: { value: 0.0001, message: "Must be positive" } })}
                                            className="form-input"
                                        />
                                        {errors.reinvestmentNav && <p className="text-red-500 text-xs italic">{errors.reinvestmentNav.message}</p>}
                                    </div>
                                )}
                            </div>
                        )}
                        {assetType === 'Bond' && transactionType === 'COUPON' && !isEditMode && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 border border-gray-200 rounded-md bg-gray-50/50">
                                <div className="form-group">
                                    <label htmlFor="couponAmount" className="form-label">Total Coupon Amount</label>
                                    <input id="couponAmount" type="number" step="any" {...register('couponAmount', { required: "Amount is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                    {errors.couponAmount && <p className="text-red-500 text-xs italic">{errors.couponAmount.message}</p>}
                                </div>
                                <div className="form-group">
                                    <label htmlFor="transaction_date_coupon" className="form-label">Payment Date</label>
                                    <input id="transaction_date_coupon" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                    {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                </div>
                            </div>
                        )}

                        {/* Corporate Action Form */}
                        {assetType === 'Stock' && transactionType === 'Corporate Action' && !isEditMode && (
                            <div className="space-y-4 p-4 border border-gray-200 rounded-md bg-gray-50/50">
                                <div className="form-group">
                                    <label htmlFor="action_type" className="form-label">Action Type</label>
                                    <select id="action_type" {...register('action_type')} className="form-input">
                                        <option value="DIVIDEND">Dividend</option>
                                        <option value="SPLIT">Stock Split</option>
                                        <option value="BONUS">Bonus Issue</option>
                                    </select>
                                </div>

                                {/* Dividend Fields */}
                                {actionType === 'DIVIDEND' && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="form-group">
                                            <label htmlFor="transaction_date_mf_dividend" className="form-label">Payment Date</label>
                                            <input id="transaction_date_mf_dividend" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                            {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="dividendAmount" className="form-label">Total Amount</label>
                                            <input id="dividendAmount" type="number" step="any" {...register('dividendAmount', { required: "Amount is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                            {errors.dividendAmount && <p className="text-red-500 text-xs italic">{errors.dividendAmount.message}</p>}
                                        </div>
                                    </div>
                                )}

                                {/* Stock Split Fields */}
                                {actionType === 'SPLIT' && (
                                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                                        <div className="form-group col-span-2">
                                            <label htmlFor="transaction_date_split" className="form-label">Effective Date</label>
                                            <input id="transaction_date_split" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                            {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                        </div>
                                        <div className="form-group col-span-2">
                                            <label className="form-label">Split Ratio</label>
                                            <div className="flex items-center space-x-2">
                                                <span className='font-medium'>New</span>
                                                <input aria-label="New shares" type="number" {...register('splitRatioNew', { required: true, valueAsNumber: true, min: 1 })} className="form-input w-20 text-center" />
                                                <span className='font-medium'>for every Old</span>
                                                <input aria-label="Old shares" type="number" {...register('splitRatioOld', { required: true, valueAsNumber: true, min: 1 })} className="form-input w-20 text-center" />
                                                <span>shares</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Bonus Issue Fields */}
                                {actionType === 'BONUS' && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                                        <div className="form-group col-span-2">
                                            <label htmlFor="transaction_date_bonus" className="form-label">Effective Date</label>
                                            <input id="transaction_date_bonus" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                            {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                        </div>
                                        <div className="form-group col-span-2">
                                            <label className="form-label">Bonus Ratio</label>
                                            <div className="flex items-center space-x-2">
                                                <span className='font-medium'>New</span>
                                                <input aria-label="New bonus shares" type="number" {...register('bonusRatioNew', { required: true, valueAsNumber: true, min: 1 })} className="form-input w-20 text-center" />
                                                <span className='font-medium'>for every Old</span>
                                                <input aria-label="Old held shares" type="number" {...register('bonusRatioOld', { required: true, valueAsNumber: true, min: 1 })} className="form-input w-20 text-center" />
                                                <span>shares</span>
                                            </div>
                                        </div>
                                    </div>
                                )}
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
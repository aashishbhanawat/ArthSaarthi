import React, { useState, useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { useCreateTransaction, useUpdateTransaction, useCreateFixedDeposit, useCreatePpfAccount, useCreateBond, } from '../../hooks/usePortfolios';
import { useCreateRecurringDeposit, useUpdateRecurringDeposit } from '../../hooks/useRecurringDeposits';
import { useUpdateFixedDeposit } from '../../hooks/useFixedDeposits';
import { useCreateAsset, useMfSearch, useAssetsByType } from '../../hooks/useAssets';
import { lookupAsset, searchStocks, AssetSearchResult, getFxRate, getAvailableLots, AvailableLot } from '../../services/portfolioApi';
import { BondCreate, BondType } from '../../types/bond';
import { Asset, MutualFundSearchResult } from '../../types/asset';
import { Transaction, TransactionCreate, TransactionUpdate, FixedDepositDetails } from '../../types/portfolio';
import { TransactionType } from '../../types/enums';
import { RecurringDepositDetails } from '../../types/recurring_deposit'; // eslint-disable-line @typescript-eslint/no-unused-vars
import { ApiError, getErrorMessage } from '../../types/api';
import Select from 'react-select';
import { formatCurrency } from '../../utils/formatting';
import { debugLog } from '../../utils/debug';

interface TransactionFormModalProps {
    portfolioId: string;
    onClose: () => void;
    isOpen: boolean;
    transactionToEdit?: Transaction;
    fixedDepositToEdit?: FixedDepositDetails;
    recurringDepositToEdit?: RecurringDepositDetails;
}

// Define the shape of our form data
type TransactionFormInputs = {
    asset_type: 'Stock' | 'Mutual Fund' | 'Fixed Deposit' | 'Recurring Deposit' | 'PPF Account' | 'Bond';
    transaction_type: 'BUY' | 'SELL' | 'DIVIDEND' | 'CONTRIBUTION' | 'Corporate Action' | 'COUPON';
    action_type: 'DIVIDEND' | 'SPLIT' | 'BONUS' | 'MERGER' | 'DEMERGER' | 'RENAME';
    quantity: number;
    price_per_unit: number;
    transaction_date: string;
    fees?: number;
    // FD-specific fields
    institutionName?: string;
    accountNumber?: string;
    principalAmount?: number;
    interestRate?: number;
    startDate?: string;
    maturityDate?: string;
    compounding_frequency?: 'Annually' | 'Half-Yearly' | 'Quarterly'; // FD - matches API type
    interest_payout?: 'Cumulative' | 'Payout'; // FD - matches API type
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
    newAssetCurrency?: string;
    details?: { [key: string]: unknown };
    // Stock DRIP fields
    isStockDividendReinvested?: boolean;
    stockReinvestmentPrice?: number;
    // Merger/Demerger/Rename fields
    mergerConversionRatio?: number;
    demergerRatio?: number;
    costAllocationPct?: number;
    newAssetSearch?: string;
};

const TransactionFormModal: React.FC<TransactionFormModalProps> = ({ portfolioId, onClose, isOpen, transactionToEdit, fixedDepositToEdit, recurringDepositToEdit }) => {
    const isEditMode = !!transactionToEdit || !!fixedDepositToEdit || !!recurringDepositToEdit;
    const { register, handleSubmit, formState: { errors }, reset, control, setValue, getValues } = useForm<TransactionFormInputs>({
        defaultValues: { asset_type: 'Stock', transaction_type: 'BUY', action_type: 'DIVIDEND', splitRatioNew: 2, splitRatioOld: 1, bonusRatioNew: 1, bonusRatioOld: 1, newAssetCurrency: 'INR' }
    });

    const queryClient = useQueryClient();
    const createTransactionMutation = useCreateTransaction();
    const updateTransactionMutation = useUpdateTransaction();
    const createAssetMutation = useCreateAsset();
    const createFixedDepositMutation = useCreateFixedDeposit();
    const updateFixedDepositMutation = useUpdateFixedDeposit();
    const createRecurringDepositMutation = useCreateRecurringDeposit();
    const updateRecurringDepositMutation = useUpdateRecurringDeposit();
    const createBondMutation = useCreateBond();
    const createPpfAccountMutation = useCreatePpfAccount();
    const [apiError, setApiError] = useState<string | null>(null);

    // Stock search state
    const [inputValue, setInputValue] = useState('');
    const [searchTerm, setSearchTerm] = useState(''); // Debounced value
    const [searchResults, setSearchResults] = useState<Asset[]>([]);
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [isSearching, setIsSearching] = useState(false);

    // New asset search state for corporate actions (merger/demerger/rename)
    const [newAssetInput, setNewAssetInput] = useState('');
    const [newAssetSearchTerm, setNewAssetSearchTerm] = useState('');
    const [newAssetResults, setNewAssetResults] = useState<Asset[]>([]);
    const [selectedNewAsset, setSelectedNewAsset] = useState<Asset | null>(null);
    const [isSearchingNewAsset, setIsSearchingNewAsset] = useState(false);

    // Watch fields to conditionally render inputs
    const assetType = useWatch({ control, name: 'asset_type' });
    const transactionType = useWatch({ control, name: 'transaction_type' });
    const actionType = useWatch({ control, name: 'action_type' });
    const isReinvested = useWatch({ control, name: 'isReinvested' });
    const transactionDate = useWatch({ control, name: 'transaction_date' });
    const quantity = useWatch({ control, name: 'quantity' });
    const pricePerUnit = useWatch({ control, name: 'price_per_unit' });
    // Stock DRIP watchers
    const isStockDividendReinvested = useWatch({ control, name: 'isStockDividendReinvested' });
    const stockReinvestmentPrice = useWatch({ control, name: 'stockReinvestmentPrice' });
    const dividendAmount = useWatch({ control, name: 'dividendAmount' });

    // --- FX Rate State & Logic ---
    const isForeignAsset = selectedAsset && selectedAsset.currency !== 'INR';
    const { data: fxRateData, isLoading: isLoadingFxRate } = useQuery({
        queryKey: ['fxRate', selectedAsset?.currency, 'INR', transactionDate],
        queryFn: () => getFxRate(selectedAsset!.currency!, 'INR', transactionDate),
        enabled: !!isForeignAsset && !!transactionDate && new Date(transactionDate).getFullYear() > 1900,
        staleTime: 1000 * 60 * 60 * 24, // 24 hours
    });

    // The getFxRate function returns the rate value directly, which might be a string.
    // Handle cases where fxRateData is an object { rate: ... } (API) or a primitive value (Tests)
    const fetchedFxRate = fxRateData && typeof fxRateData === 'object' && 'rate' in fxRateData
        ? Number((fxRateData as { rate: number | string }).rate)
        : (fxRateData ? Number(fxRateData) : undefined);

    // Editable FX rate: pre-populated from API, user can override
    const [editableFxRate, setEditableFxRate] = useState<number | undefined>(undefined);

    // Sync editable FX rate when fetched rate changes (but don't override user edits)
    useEffect(() => {
        if (fetchedFxRate && !editableFxRate) {
            setEditableFxRate(fetchedFxRate);
        }
    }, [fetchedFxRate, editableFxRate]);

    // Reset editable FX rate when asset or date changes
    useEffect(() => {
        setEditableFxRate(undefined);
    }, [selectedAsset, transactionDate]);

    // Use editable rate if set, otherwise fall back to fetched rate
    const fxRate = editableFxRate ?? fetchedFxRate;

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

    // --- Tax Lot Accounting State ---
    const [availableLots, setAvailableLots] = useState<AvailableLot[]>([]);
    const [lotSelections, setLotSelections] = useState<{ [lotId: string]: number }>({});
    const [isLoadingLots, setIsLoadingLots] = useState(false);

    useEffect(() => {
        if (isEditMode) {
            if (transactionToEdit) {
                // Format date for input[type=date] which expects 'YYYY-MM-DD'
                // Extract date portion directly from API string to avoid timezone conversion issues
                const formattedDate = transactionToEdit.transaction_date.split('T')[0];

                // Map API asset_type to form asset_type
                // API returns: 'BOND', 'Mutual Fund', 'PPF', 'Stock', etc.
                // Form expects: 'Bond', 'Mutual Fund', 'PPF Account', 'Stock', etc.
                const rawAssetType = transactionToEdit.asset.asset_type;
                const assetTypeMap: { [key: string]: TransactionFormInputs['asset_type'] } = {
                    'BOND': 'Bond',
                    'Bond': 'Bond',
                    'Mutual Fund': 'Mutual Fund',
                    'PPF': 'PPF Account',
                    'Stock': 'Stock',
                };
                const computedAssetType = assetTypeMap[rawAssetType] || 'Stock';
                debugLog('transaction', 'Edit mode - asset object:', transactionToEdit.asset);
                debugLog('transaction', `Edit mode - rawAssetType: "${rawAssetType}", computedAssetType: "${computedAssetType}"`);

                reset({
                    transaction_type: transactionToEdit.transaction_type as TransactionFormInputs['transaction_type'],
                    asset_type: computedAssetType,
                    quantity: Number(transactionToEdit.quantity),
                    price_per_unit: Number(transactionToEdit.price_per_unit),
                    transaction_date: formattedDate,
                    fees: Number(transactionToEdit.fees),
                    details: transactionToEdit.details ?? undefined,
                    // PPF contribution fields - quantity represents the contribution amount
                    ...(computedAssetType === 'PPF Account' && {
                        contributionAmount: Number(transactionToEdit.quantity),
                        contributionDate: formattedDate,
                    }),
                });
                setSelectedAsset(transactionToEdit.asset);
                setInputValue(transactionToEdit.asset.name);
                // For Mutual Fund transactions, also set selectedMf so the react-select shows the value
                if (computedAssetType === 'Mutual Fund') {
                    setSelectedMf({
                        name: transactionToEdit.asset.name,
                        ticker_symbol: transactionToEdit.asset.ticker_symbol,
                        asset_type: 'Mutual Fund',
                    });
                }
            } else if (fixedDepositToEdit) {
                reset({
                    asset_type: 'Fixed Deposit',
                    institutionName: fixedDepositToEdit.name,
                    accountNumber: fixedDepositToEdit.account_number || '',
                    principalAmount: Number(fixedDepositToEdit.principal_amount),
                    interestRate: Number(fixedDepositToEdit.interest_rate),
                    startDate: fixedDepositToEdit.start_date,
                    maturityDate: fixedDepositToEdit.maturity_date,
                    compounding_frequency: fixedDepositToEdit.compounding_frequency as any, // eslint-disable-line @typescript-eslint/no-explicit-any
                    interest_payout: fixedDepositToEdit.interest_payout as any, // eslint-disable-line @typescript-eslint/no-explicit-any
                });
            } else if (recurringDepositToEdit) {
                reset({
                    asset_type: 'Recurring Deposit',
                    rdName: recurringDepositToEdit.name,
                    rdAccountNumber: recurringDepositToEdit.account_number || '',
                    monthlyInstallment: Number(recurringDepositToEdit.monthly_installment),
                    rdInterestRate: Number(recurringDepositToEdit.interest_rate),
                    rdStartDate: recurringDepositToEdit.start_date,
                    tenureMonths: Number(recurringDepositToEdit.tenure_months),
                });
            }
        }
    }, [isEditMode, transactionToEdit, fixedDepositToEdit, recurringDepositToEdit, reset]);

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
        searchStocks(searchTerm, assetTypeFilter)
            .then(data => setSearchResults(data as Asset[]))  // Cast to Asset[] for display compatibility
            .catch(() => setSearchResults([]))
            .finally(() => setIsSearching(false));
    }, [searchTerm, selectedAsset, assetType]);

    const handleSelectAsset = async (asset: Asset | AssetSearchResult) => {
        // If from Yahoo search (external), call lookupAsset to create it
        const searchResult = asset as AssetSearchResult;
        if (searchResult.source === 'yahoo') {
            try {
                const assetTypeFilter = assetType === 'Bond' ? 'BOND' : (assetType === 'Stock' ? 'STOCK' : undefined);
                const createdAssets = await lookupAsset(searchResult.ticker_symbol, assetTypeFilter, true);  // forceExternal
                if (createdAssets.length > 0) {
                    setSelectedAsset(createdAssets[0]);
                    setInputValue(createdAssets[0].name);
                }
            } catch {
                // Fallback to using the search result as-is
                setSelectedAsset(asset as Asset);
                setInputValue(asset.name);
            }
        } else {
            setSelectedAsset(asset as Asset);
            setInputValue(asset.name);
        }
        setSearchResults([]);
    };

    const handleClearSelectedAsset = () => {
        setSelectedAsset(null);
        setInputValue('');
    };

    // --- New Asset Search for Corporate Actions ---
    // Debounce new asset input
    useEffect(() => {
        const handler = setTimeout(() => {
            setNewAssetSearchTerm(newAssetInput);
        }, 300);
        return () => clearTimeout(handler);
    }, [newAssetInput]);

    // Search for new asset
    useEffect(() => {
        if (newAssetSearchTerm.length < 2 || selectedNewAsset) {
            setNewAssetResults([]);
            return;
        }
        setIsSearchingNewAsset(true);
        searchStocks(newAssetSearchTerm, 'STOCK')
            .then(data => setNewAssetResults(data as Asset[]))
            .catch(() => setNewAssetResults([]))
            .finally(() => setIsSearchingNewAsset(false));
    }, [newAssetSearchTerm, selectedNewAsset]);

    const handleSelectNewAsset = async (asset: Asset | AssetSearchResult) => {
        const searchResult = asset as AssetSearchResult;
        if (searchResult.source === 'yahoo') {
            try {
                const createdAssets = await lookupAsset(searchResult.ticker_symbol, 'STOCK', true);  // forceExternal
                if (createdAssets.length > 0) {
                    setSelectedNewAsset(createdAssets[0]);
                    setNewAssetInput(createdAssets[0].ticker_symbol || createdAssets[0].name);
                    setValue('newAssetSearch', createdAssets[0].ticker_symbol || createdAssets[0].name);
                }
            } catch {
                setSelectedNewAsset(asset as Asset);
                setNewAssetInput(asset.ticker_symbol || asset.name);
                setValue('newAssetSearch', asset.ticker_symbol || asset.name);
            }
        } else {
            setSelectedNewAsset(asset as Asset);
            setNewAssetInput(asset.ticker_symbol || asset.name);
            setValue('newAssetSearch', asset.ticker_symbol || asset.name);
        }
        setNewAssetResults([]);
    };

    const handleClearNewAsset = () => {
        setSelectedNewAsset(null);
        setNewAssetInput('');
        setValue('newAssetSearch', '');
    };

    const handleSelectMf = (mf: MutualFundSearchResult | null) => {
        setSelectedMf(mf);
    };

    useEffect(() => {
        if (selectedAsset && assetType === 'Bond') {
            // Populate the bond-specific fields when a bond asset is selected
            setValue('bondType', selectedAsset.bond?.bond_type || undefined, { shouldValidate: true });
            setValue('isin', selectedAsset.isin || '', { shouldValidate: true });
            setValue('couponRate', selectedAsset.bond?.coupon_rate || undefined, { shouldValidate: true });
            setValue('faceValue', selectedAsset.bond?.face_value || undefined, { shouldValidate: true });
            setValue('bondMaturityDate', selectedAsset.bond?.maturity_date ? new Date(selectedAsset.bond.maturity_date).toISOString().split('T')[0] : '', { shouldValidate: true });
        }
    }, [selectedAsset, assetType, setValue]);

    // Fetch available lots for SELL transactions
    useEffect(() => {
        if (selectedAsset && selectedAsset.id && transactionType === 'SELL' && (assetType === 'Stock' || assetType === 'Mutual Fund')) {
            setIsLoadingLots(true);
            getAvailableLots(selectedAsset.id)
                .then(lots => {
                    setAvailableLots(lots);
                    setLotSelections({});
                })
                .catch(err => console.error("Failed to fetch lots", err))
                .finally(() => setIsLoadingLots(false));
        } else {
            setAvailableLots([]);
            setLotSelections({});
        }
    }, [selectedAsset, transactionType, assetType]);

    // Helper to calculate total selected quantity
    const totalSelectedQty = Object.values(lotSelections).reduce((sum, qty) => sum + qty, 0);

    const handleLotChange = (lotId: string, qty: number) => {
        if (qty < 0) return;
        setLotSelections(prev => ({
            ...prev,
            [lotId]: qty
        }));
    };

    const applyFIFO = () => {
        let remaining = quantity;
        const newSelections: { [id: string]: number } = {};
        // Sort by date ascending
        const sortedLots = [...availableLots].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        for (const lot of sortedLots) {
            if (remaining <= 0) break;
            const take = Math.min(remaining, lot.available_quantity);
            if (take > 0) {
                newSelections[lot.id] = take;
                remaining -= take;
            }
        }
        setLotSelections(newSelections);
    };

    const applyLIFO = () => {
        let remaining = quantity;
        const newSelections: { [id: string]: number } = {};
        // Sort by date descending
        const sortedLots = [...availableLots].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

        for (const lot of sortedLots) {
            if (remaining <= 0) break;
            const take = Math.min(remaining, lot.available_quantity);
            if (take > 0) {
                newSelections[lot.id] = take;
                remaining -= take;
            }
        }
        setLotSelections(newSelections);
    };

    const applyHighestCost = () => {
        let remaining = quantity;
        const newSelections: { [id: string]: number } = {};
        // Sort by price descending
        const sortedLots = [...availableLots].sort((a, b) => b.price_per_unit - a.price_per_unit);

        for (const lot of sortedLots) {
            if (remaining <= 0) break;
            const take = Math.min(remaining, lot.available_quantity);
            if (take > 0) {
                newSelections[lot.id] = take;
                remaining -= take;
            }
        }
        setLotSelections(newSelections);
    };


    const handleCreateAsset = () => {
        if (inputValue) {
            setSelectedAsset({
                name: inputValue,
                ticker_symbol: inputValue.toUpperCase(),
                currency: getValues('newAssetCurrency') || 'INR'
            } as Asset);
        }
    };

    const onSubmit = (data: TransactionFormInputs) => {
        // Defensively coalesce NaN to 0. This can happen if the fees input is left blank.
        if (isNaN(data.fees as number)) {
            data.fees = 0;
        }

        const details = isForeignAsset && fxRate && !isNaN(fxRate) ? { fx_rate: fxRate } : undefined;

        const mutationOptions = {
            onSuccess: () => {
                // Always invalidate portfolio queries on success to refetch holdings, summary, etc.
                queryClient.invalidateQueries({ queryKey: ['portfolio', portfolioId] });
                // More specific invalidations are handled by the hook itself.
                onClose();
            },
            onError: (error: ApiError) => {
                const defaultMessage = isEditMode
                    ? 'An unexpected error occurred while updating the transaction'
                    : 'An unexpected error occurred while adding the transaction';
                setApiError(getErrorMessage(error) || defaultMessage);
            }
        };

        // --- Corporate Action Logic ---
        if (assetType === 'Stock' && transactionType === 'Corporate Action') {
            if (!selectedAsset?.id) {
                setApiError("Please select a stock to apply the corporate action to.");
                return;
            }

            let payload: TransactionCreate | TransactionCreate[];

            switch (data.action_type) {
                case 'DIVIDEND':
                    if (data.isStockDividendReinvested && data.stockReinvestmentPrice && data.stockReinvestmentPrice > 0) {
                        // Stock DRIP: Create two transactions - DIVIDEND + BUY
                        const reinvestedQuantity = data.dividendAmount! / data.stockReinvestmentPrice;
                        const dividendTx: TransactionCreate = {
                            asset_id: selectedAsset.id,
                            transaction_type: 'DIVIDEND' as TransactionType,
                            quantity: data.dividendAmount!,
                            price_per_unit: 1,
                            transaction_date: new Date(data.transaction_date).toISOString(),
                            details,
                        };
                        const buyTx: TransactionCreate = {
                            asset_id: selectedAsset.id,
                            transaction_type: 'BUY' as TransactionType,
                            quantity: reinvestedQuantity,
                            price_per_unit: data.stockReinvestmentPrice,
                            transaction_date: new Date(data.transaction_date).toISOString(),
                            details,
                        };
                        payload = [dividendTx, buyTx];
                    } else {
                        // Regular cash dividend
                        payload = {
                            asset_id: selectedAsset.id,
                            transaction_type: 'DIVIDEND' as TransactionType,
                            quantity: data.dividendAmount!,
                            price_per_unit: 1,
                            transaction_date: new Date(data.transaction_date).toISOString(),
                            details,
                        };
                    }
                    break;
                case 'SPLIT':
                    payload = {
                        asset_id: selectedAsset.id,
                        transaction_type: 'SPLIT' as TransactionType,
                        quantity: data.splitRatioNew!,
                        price_per_unit: data.splitRatioOld!, // Repurposed for old part of ratio
                        transaction_date: new Date(data.transaction_date).toISOString(),
                        details,
                    };
                    break;
                case 'BONUS':
                    payload = {
                        asset_id: selectedAsset.id,
                        transaction_type: 'BONUS' as TransactionType,
                        quantity: data.bonusRatioNew!,
                        price_per_unit: data.bonusRatioOld!, // Repurposed for old shares held
                        transaction_date: new Date(data.transaction_date).toISOString(),
                        details,
                    };
                    break;
                case 'MERGER':
                    // Merger: quantity = conversion ratio, details contains new_asset_id
                    // Note: new asset needs to exist or be created first via ticker lookup
                    payload = {
                        asset_id: selectedAsset.id,
                        transaction_type: 'MERGER' as TransactionType,
                        quantity: data.mergerConversionRatio!,
                        price_per_unit: 1, // Not used for merger
                        transaction_date: new Date(data.transaction_date).toISOString(),
                        details: {
                            ...details,
                            new_asset_ticker: data.newAssetSearch,
                        },
                    };
                    break;
                case 'DEMERGER':
                    // Demerger: quantity = ratio, details contains new_asset_id and cost allocation
                    payload = {
                        asset_id: selectedAsset.id,
                        transaction_type: 'DEMERGER' as TransactionType,
                        quantity: data.demergerRatio!,
                        price_per_unit: 1, // Not used for demerger
                        transaction_date: new Date(data.transaction_date).toISOString(),
                        details: {
                            ...details,
                            new_asset_ticker: data.newAssetSearch,
                            cost_allocation_pct: data.costAllocationPct,
                        },
                    };
                    break;
                case 'RENAME':
                    // Rename: transfers holdings to new ticker
                    payload = {
                        asset_id: selectedAsset.id,
                        transaction_type: 'RENAME' as TransactionType,
                        quantity: 1, // Not used for rename
                        price_per_unit: 1, // Not used for rename
                        transaction_date: new Date(data.transaction_date).toISOString(),
                        details: {
                            ...details,
                            new_asset_ticker: data.newAssetSearch,
                        },
                    };
                    break;
                default:
                    setApiError("Invalid corporate action type selected.");
                    return;
            }

            // Handle both single transaction and array of transactions (DRIP case)
            if (Array.isArray(payload)) {
                // For DRIP: create multiple transactions sequentially
                payload.forEach(tx => createTransactionMutation.mutate({ portfolioId, data: tx }, mutationOptions));
            } else {
                createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
            }
            return; // Exit after handling corporate action
        }

        // --- Bond Coupon Logic ---
        if (assetType === 'Bond' && transactionType === 'COUPON') {
            if (!selectedAsset?.id) {
                setApiError("Please select a bond to apply the coupon to.");
                return;
            }
            const payload: TransactionCreate = {
                asset_id: selectedAsset.id,
                transaction_type: 'COUPON' as TransactionType,
                quantity: data.couponAmount!, // Repurposed for total cash amount
                price_per_unit: 1,
                transaction_date: new Date(data.transaction_date).toISOString(),
                details,
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
                    asset_type: 'Mutual Fund' as const,
                    transaction_type: 'DIVIDEND' as TransactionType,
                    quantity: data.mfDividendAmount!,
                    price_per_unit: 1, // Price is 1 for dividend amount
                    transaction_date: new Date(data.transaction_date).toISOString(),
                    details,
                };

                const reinvestedQuantity = data.mfDividendAmount! / data.reinvestmentNav!;
                const buyTx: TransactionCreate = {
                    ticker_symbol: selectedMf.ticker_symbol,
                    asset_type: 'Mutual Fund' as const,
                    transaction_type: 'BUY' as TransactionType,
                    quantity: reinvestedQuantity,
                    price_per_unit: data.reinvestmentNav!,
                    transaction_date: new Date(data.transaction_date).toISOString(),
                    details,
                };
                payload = [dividendTx, buyTx];
            } else {
                // For simple cash dividend, create only one transaction.
                payload = { ticker_symbol: selectedMf.ticker_symbol, asset_type: 'Mutual Fund' as const, transaction_type: 'DIVIDEND' as TransactionType, quantity: data.mfDividendAmount!, price_per_unit: 1, transaction_date: new Date(data.transaction_date).toISOString(), details };
            }

            // Handle both single transaction and array of transactions (DRIP case)
            if (Array.isArray(payload)) {
                payload.forEach(tx => createTransactionMutation.mutate({ portfolioId, data: tx }, mutationOptions));
            } else {
                createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
            }
            return;
        }

        if (assetType === 'PPF Account') {
            if (existingPpfAsset) {
                // Contribution to an existing PPF account
                const payload = {
                    asset_id: existingPpfAsset.id!,
                    transaction_type: 'CONTRIBUTION' as TransactionType,
                    quantity: data.contributionAmount!,
                    price_per_unit: 1,
                    transaction_date: new Date(data.contributionDate!).toISOString(),
                    details,
                };

                if (isEditMode && transactionToEdit) {
                    // Update existing contribution
                    const updatePayload: TransactionUpdate = {
                        quantity: data.contributionAmount!,
                        price_per_unit: 1,
                        transaction_date: new Date(data.contributionDate!).toISOString(),
                        details,
                    };
                    updateTransactionMutation.mutate({
                        portfolioId,
                        transactionId: transactionToEdit.id,
                        data: updatePayload
                    }, mutationOptions);
                } else {
                    // Add new contribution
                    createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
                }
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
            if (isEditMode && fixedDepositToEdit) {
                updateFixedDepositMutation.mutate({
                    portfolioId,
                    fdId: fixedDepositToEdit.id,
                    data: {
                        name: data.institutionName!,
                        account_number: data.accountNumber!,
                        principal_amount: data.principalAmount!,
                        interest_rate: data.interestRate!,
                        start_date: data.startDate!,
                        maturity_date: data.maturityDate!,
                        compounding_frequency: data.compounding_frequency,
                        interest_payout: data.interest_payout
                    }
                }, mutationOptions);
            } else {
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
            }
        } else if (assetType === 'Recurring Deposit') {
            if (isEditMode && recurringDepositToEdit) {
                updateRecurringDepositMutation.mutate({
                    rdId: recurringDepositToEdit.id,
                    data: {
                        name: data.rdName!,
                        account_number: data.rdAccountNumber!,
                        monthly_installment: data.monthlyInstallment!,
                        interest_rate: data.rdInterestRate!,
                        start_date: data.rdStartDate!,
                        tenure_months: data.tenureMonths!,
                    }
                }, mutationOptions);
            } else {
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
            }
        } else if (assetType === 'Bond') {
            // Handle Bond edit mode first
            if (isEditMode && transactionToEdit) {
                const updatePayload: TransactionUpdate = {
                    quantity: data.quantity,
                    price_per_unit: data.price_per_unit,
                    transaction_date: new Date(data.transaction_date).toISOString(),
                    fees: data.fees || 0,
                    details,
                };
                updateTransactionMutation.mutate({
                    portfolioId,
                    transactionId: transactionToEdit.id,
                    data: updatePayload
                }, mutationOptions);
                return;
            }

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
                    isin: data.isin ?? null,
                    payment_frequency: null,
                    first_payment_date: null,
                };
                const transactionData: TransactionCreate = { asset_id: assetId, transaction_type: 'BUY' as TransactionType, quantity: data.quantity, price_per_unit: data.price_per_unit, transaction_date: new Date(data.transaction_date).toISOString(), fees: data.fees || 0, details };

                // If the asset already exists and its bond details are complete (i.e., not a placeholder),
                // we just add a new transaction. Otherwise, we use the bond creation endpoint which
                // also handles updating (upserting) the bond details along with creating the first transaction.
                const isBondDetailComplete = selectedAsset.bond && selectedAsset.bond.maturity_date && selectedAsset.bond.maturity_date !== '1970-01-01';
                if (isBondDetailComplete) {
                    const payload: TransactionCreate = { ...transactionData, asset_id: selectedAsset.id };
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
                    transaction_date: new Date(data.transaction_date).toISOString(), // eslint-disable-line @typescript-eslint/no-explicit-any
                    fees: data.fees || 0,
                    details: isForeignAsset && fxRate && !isNaN(fxRate) ? { ...(transactionToEdit.details || {}), fx_rate: fxRate } : (transactionToEdit.details ?? undefined),
                };
                updateTransactionMutation.mutate({ portfolioId, transactionId: transactionToEdit.id, data: payload }, mutationOptions);
            } else {
                const commonPayload = {
                    transaction_type: data.transaction_type as unknown as TransactionType,
                    quantity: data.quantity,
                    price_per_unit: data.price_per_unit,
                    transaction_date: new Date(data.transaction_date).toISOString(),
                    fees: data.fees || 0,
                    details,
                    links: totalSelectedQty > 0 ? Object.entries(lotSelections)
                        .filter(([, qty]) => qty > 0)
                        .map(([buyTxId, qty]) => ({
                            buy_transaction_id: buyTxId,
                            quantity: qty
                        })) : undefined
                };

                const createTransactionForAsset = (assetId: string) => {
                    const payload: TransactionCreate = { ...commonPayload, asset_id: assetId };
                    createTransactionMutation.mutate({ portfolioId, data: payload }, mutationOptions);
                };

                if (assetType === 'Stock' && selectedAsset) {
                    if (selectedAsset.id) {
                        // Asset already exists
                        createTransactionForAsset(selectedAsset.id);
                    } else {
                        // Asset needs to be created first
                        createAssetMutation.mutate(
                            {
                                ticker_symbol: selectedAsset.ticker_symbol,
                                name: selectedAsset.name,
                                asset_type: 'STOCK',
                                currency: data.newAssetCurrency || 'INR',
                            },
                            {
                                onSuccess: (newAsset) => createTransactionForAsset(newAsset.id),
                                onError: () => setApiError(`Failed to create asset "${selectedAsset.name}".`),
                            }
                        );
                    }
                } else if (assetType === 'Mutual Fund' && selectedMf) {
                    const payload: TransactionCreate = { ...commonPayload, ticker_symbol: selectedMf.ticker_symbol, asset_type: 'Mutual Fund' as const };
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
                <h2 id="transaction-form-modal-title" className="text-2xl font-bold mb-4 dark:text-gray-100">{isEditMode ? 'Edit' : 'Add'} Transaction</h2>
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
                                                        {isSearching && <div className="absolute z-20 w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md mt-1 p-2 shadow-lg dark:text-gray-200">Searching...</div>}
                                                        {!isSearching && searchResults.length > 0 && !selectedAsset && (
                                                            <ul className="absolute z-20 w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md mt-1 max-h-40 overflow-y-auto shadow-lg">
                                                                {searchResults.map(asset => (
                                                                    <li key={asset.id} onClick={() => handleSelectAsset(asset)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-600 cursor-pointer dark:text-gray-200">
                                                                        {asset.name} ({asset.ticker_symbol})
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        )}
                                                        {!isSearching && searchResults.length === 0 && inputValue.length > 1 && !selectedAsset && (
                                                            <div className="absolute z-20 w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md mt-1 p-3 shadow-lg space-y-2">
                                                                <p className="text-sm text-gray-600 dark:text-gray-300">No asset found. Create a new one:</p>
                                                                <div className="form-group">
                                                                    <label htmlFor="newAssetCurrency" className="form-label text-xs">Currency</label>
                                                                    <select id="newAssetCurrency" {...register('newAssetCurrency')} className="form-input form-input-sm">
                                                                        <option value="INR">INR</option>
                                                                        <option value="USD">USD</option>
                                                                        <option value="EUR">EUR</option>
                                                                        <option value="GBP">GBP</option>
                                                                        <option value="JPY">JPY</option>
                                                                    </select>
                                                                </div>
                                                                <button type="button" onClick={handleCreateAsset} className="btn btn-secondary btn-sm w-full" disabled={createAssetMutation.isPending} data-testid="create-new-asset-button">
                                                                    {createAssetMutation.isPending ? 'Creating...' : `Confirm & Create Asset "${inputValue.toUpperCase()}"`}
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
                                                    control: (base, state) => ({
                                                        ...base,
                                                        backgroundColor: state.isDisabled
                                                            ? (document.documentElement.classList.contains('dark') ? '#4b5563' : '#f3f4f6')
                                                            : (document.documentElement.classList.contains('dark') ? '#374151' : '#fff'),
                                                        borderColor: document.documentElement.classList.contains('dark') ? '#4b5563' : '#d1d5db',
                                                        minHeight: '42px',
                                                        color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#111',
                                                    }),
                                                    menu: (base) => ({
                                                        ...base,
                                                        zIndex: 30,
                                                        backgroundColor: document.documentElement.classList.contains('dark') ? '#374151' : '#fff',
                                                    }),
                                                    option: (base, state) => ({
                                                        ...base,
                                                        backgroundColor: state.isFocused
                                                            ? (document.documentElement.classList.contains('dark') ? '#4b5563' : '#e5e7eb')
                                                            : 'transparent',
                                                        color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#111',
                                                    }),
                                                    singleValue: (base, state) => ({
                                                        ...base,
                                                        color: state.isDisabled
                                                            ? (document.documentElement.classList.contains('dark') ? '#d1d5db' : '#4b5563')
                                                            : (document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#111'),
                                                    }),
                                                    input: (base) => ({
                                                        ...base,
                                                        color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#111',
                                                    }),
                                                    placeholder: (base) => ({
                                                        ...base,
                                                        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280',
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

                                                                &times;
                                                            </button>
                                                        )}
                                                        {isSearching && <div className="absolute z-20 w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md mt-1 p-2 shadow-lg dark:text-gray-200">Searching...</div>}
                                                        {!isSearching && searchResults.length > 0 && !selectedAsset && (
                                                            <ul className="absolute z-20 w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md mt-1 max-h-40 overflow-y-auto shadow-lg" data-testid="bond-search-results">
                                                                {searchResults.map(asset => (
                                                                    <li key={asset.id} onClick={() => handleSelectAsset(asset)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-600 cursor-pointer dark:text-gray-200">
                                                                        {asset.name} ({asset.ticker_symbol})
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        )}
                                                        {!isSearching && searchResults.length > 0 && searchResults.filter(a => a.asset_type === 'BOND').length === 0 && !selectedAsset && assetType === 'Bond' && (
                                                            <div className="absolute z-20 w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md mt-1 p-2 shadow-lg" data-testid="no-bond-results">
                                                                <p className="text-sm text-gray-500 dark:text-gray-400">No bond assets found for "{inputValue}" .</p>
                                                            </div>
                                                        )}
                                                        {!isSearching && searchResults.length === 0 && inputValue.length > 1 && !selectedAsset && (
                                                            <div className="absolute z-20 w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md mt-1 p-2 shadow-lg" data-testid="create-new-asset-section">
                                                                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">No {String(assetType).toLowerCase()} found. You can create it.</p>
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

                        {/* Foreign Asset Conversion Section */}
                        {isForeignAsset && (
                            <div className="p-4 border rounded-md bg-blue-50 dark:bg-blue-900/30 dark:border-blue-700 mb-4">
                                <h3 className="font-semibold text-lg text-blue-800 dark:text-blue-300">INR Conversion</h3>
                                <div className="grid grid-cols-2 gap-4 mt-2">
                                    <div className="form-group">
                                        <label htmlFor="editableFxRate" className="form-label text-blue-700 dark:text-blue-400">FX Rate ({selectedAsset.currency}-INR)</label>
                                        {isLoadingFxRate ? (
                                            <div className="form-input bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200">Fetching...</div>
                                        ) : (
                                            <input
                                                id="editableFxRate"
                                                type="number"
                                                step="any"
                                                value={editableFxRate ?? ''}
                                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditableFxRate(e.target.value ? Number(e.target.value) : undefined)}
                                                className="form-input"
                                                data-testid="fx-rate-input"
                                                placeholder="Enter FX rate"
                                            />
                                        )}
                                        <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">Auto-fetched rate: {fetchedFxRate ?? 'N/A'}</p>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label text-blue-700 dark:text-blue-400">Total (INR)</label>
                                        <div className="form-input bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200 font-bold">
                                            {(() => {
                                                if (!fxRate || isNaN(fxRate)) return '0.00';
                                                // For corporate action dividends, use dividendAmount
                                                if (transactionType === 'Corporate Action' && actionType === 'DIVIDEND' && dividendAmount > 0) {
                                                    return formatCurrency(dividendAmount * fxRate, 'INR');
                                                }
                                                // For regular transactions, use quantity * pricePerUnit
                                                if (quantity > 0 && pricePerUnit > 0) {
                                                    return formatCurrency(quantity * pricePerUnit * fxRate, 'INR');
                                                }
                                                return '0.00';
                                            })()}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {(assetType === 'PPF Account') && (
                            isLoadingPpfAssets ? <p className="dark:text-gray-300">Loading PPF details...</p> : (
                                existingPpfAsset ? (
                                    <div>
                                        <div className="p-4 border rounded-md bg-gray-50 dark:bg-gray-700 dark:border-gray-600 mb-4">
                                            <h3 className="font-semibold text-lg text-gray-800 dark:text-gray-100">Existing PPF Account</h3>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">Institution: {existingPpfAsset.name}</p>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">Account #: {existingPpfAsset.account_number}</p>
                                        </div>
                                        <h3 className="font-semibold text-lg text-gray-800 dark:text-gray-100 mb-2">
                                            {isEditMode ? 'Edit Contribution' : 'Add New Contribution'}
                                        </h3>
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
                                        <h3 className="font-semibold text-lg text-gray-800 dark:text-gray-100 mb-2">Create Your PPF Account</h3>
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

                        {/* For MF, we need the buy/sell/dividend dropdown. This should be outside the conditional block below. */}
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

                        {/* Standard BUY/SELL Form */}
                        {((assetType === 'Stock' && transactionType !== 'Corporate Action') || (assetType === 'Mutual Fund' && transactionType !== 'DIVIDEND') || (assetType === 'Bond' && transactionType !== 'COUPON')) && (
                            <div className="space-y-4 p-4 border border-gray-200 rounded-md bg-gray-50/50">
                                {(
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="form-group">
                                            <label htmlFor="quantity" className="form-label">Quantity</label>                                        <input id="quantity" type="number" step="any" {...register('quantity', { required: "Quantity is required", valueAsNumber: true, min: { value: 0.000001, message: "Must be positive" } })} className="form-input" />
                                            {errors.quantity && <p className="text-red-500 text-xs italic">{errors.quantity.message}</p>}
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="price_per_unit" className="form-label">Price per Unit {isForeignAsset ? `(${selectedAsset.currency})` : ''}</label>
                                            <input id="price_per_unit" type="number" step="any" {...register('price_per_unit', { required: transactionType !== 'Corporate Action', valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                            {errors.price_per_unit && <p className="text-red-500 text-xs italic">{errors.price_per_unit.message}</p>}
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="transaction_date_standard" className="form-label">Date</label>                                        <input id="transaction_date_standard" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                            {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                        </div>
                                        <div className="form-group">
                                            <label htmlFor="fees" className="form-label">Fees (optional)</label>
                                            <input id="fees" type="number" step="any" {...register('fees', { valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                            {errors.fees && <p className="text-red-500 text-xs italic">{errors.fees.message}</p>}
                                        </div>
                                    </div>
                                )}

                                {/* Tax Lot Selection Section */}
                                {transactionType === 'SELL' && (assetType === 'Stock' || assetType === 'Mutual Fund') && (
                                    <div className="mt-6 border-t dark:border-gray-600 pt-4">
                                        <div className="flex justify-between items-center mb-2">
                                            <h4 className="font-semibold text-gray-700 dark:text-gray-200">Select Tax Lots (Optional)</h4>
                                            <div className="space-x-2">
                                                <button type="button" onClick={applyFIFO} className="text-xs bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 dark:text-gray-200 px-2 py-1 rounded">FIFO</button>
                                                <button type="button" onClick={applyLIFO} className="text-xs bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 dark:text-gray-200 px-2 py-1 rounded">LIFO</button>
                                                <button type="button" onClick={applyHighestCost} className="text-xs bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 dark:text-gray-200 px-2 py-1 rounded">Highest Cost</button>
                                            </div>
                                        </div>

                                        {isLoadingLots ? (
                                            <p className="text-sm text-gray-500 dark:text-gray-400">Loading available lots...</p>
                                        ) : availableLots.length === 0 ? (
                                            <p className="text-sm text-gray-500 dark:text-gray-400">No available lots found.</p>
                                        ) : (
                                            <div className="overflow-x-auto max-h-60 border dark:border-gray-600 rounded-md">
                                                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                                                    <thead className="bg-gray-50 dark:bg-gray-700">
                                                        <tr>
                                                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Date</th>
                                                            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Avail</th>
                                                            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Cost</th>
                                                            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Sell Qty</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                                                        {availableLots.map((lot) => (
                                                            <tr key={lot.id}>
                                                                <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">
                                                                    {new Date(lot.date).toLocaleDateString()}
                                                                </td>
                                                                <td className="px-3 py-2 whitespace-nowrap text-xs text-right text-gray-900">
                                                                    {Number(lot.available_quantity).toFixed(4)}
                                                                </td>
                                                                <td className="px-3 py-2 whitespace-nowrap text-xs text-right text-gray-900">
                                                                    {formatCurrency(Number(lot.price_per_unit), selectedAsset?.currency || 'INR')}
                                                                </td>
                                                                <td className="px-3 py-2 whitespace-nowrap text-right">
                                                                    <input
                                                                        type="number"
                                                                        step="any"
                                                                        min="0"
                                                                        max={Number(lot.available_quantity)}
                                                                        value={lotSelections[lot.id] || ''}
                                                                        onChange={(e) => handleLotChange(lot.id, parseFloat(e.target.value) || 0)}
                                                                        className="w-20 text-right text-sm border-gray-300 dark:border-gray-500 dark:bg-gray-700 dark:text-gray-200 rounded-md focus:ring-blue-500 focus:border-blue-500 p-1 border"
                                                                    />
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        )}
                                        <div className="mt-2 text-right text-sm text-gray-600 dark:text-gray-400">
                                            Selected: <span className="font-medium">{totalSelectedQty.toFixed(4)}</span>
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
                                        <label htmlFor="mfDividendAmount" className="form-label">Total Dividend Amount {isForeignAsset ? `(${selectedAsset.currency})` : ''}</label>
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
                                    <label htmlFor="couponAmount" className="form-label">Total Coupon Amount {isForeignAsset ? `(${selectedAsset.currency})` : ''}</label>
                                    <input id="couponAmount" type="number" step="any" {...register('couponAmount', { required: "Amount is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                    {errors.couponAmount && <p className="text-red-500 text-xs italic">{errors.couponAmount.message}</p>}
                                </div>
                                <div className="form-group">
                                    <label htmlFor="transaction_date_coupon" className="form-label">Date</label>
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
                                        {/* Hide non-dividend corporate actions for foreign stocks */}
                                        {!isForeignAsset && (
                                            <>
                                                <option value="SPLIT">Stock Split</option>
                                                <option value="BONUS">Bonus Issue</option>
                                                <option value="MERGER">Merger/Amalgamation</option>
                                                <option value="DEMERGER">Demerger/Spin-off</option>
                                                <option value="RENAME">Ticker Rename</option>
                                            </>
                                        )}
                                    </select>
                                </div>

                                {/* Dividend Fields */}
                                {actionType === 'DIVIDEND' && (
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="form-group">
                                                <label htmlFor="transaction_date_stock_dividend" className="form-label">Payment Date</label>
                                                <input id="transaction_date_stock_dividend" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                                {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                            </div>
                                            <div className="form-group">
                                                <div className="flex items-baseline">
                                                    <label htmlFor="dividendAmount" className="form-label">Total Amount</label>
                                                    {isForeignAsset && <span className="text-gray-500 text-sm ml-1">({selectedAsset.currency})</span>}
                                                </div>
                                                <input id="dividendAmount" type="number" step="any" {...register('dividendAmount', { required: "Amount is required", valueAsNumber: true, min: { value: 0, message: "Must be non-negative" } })} className="form-input" />
                                                {errors.dividendAmount && <p className="text-red-500 text-xs italic">{errors.dividendAmount.message}</p>}
                                            </div>
                                        </div>
                                        {/* Stock DRIP Section */}
                                        <div className="flex items-center space-x-2">
                                            <input id="isStockDividendReinvested" type="checkbox" {...register('isStockDividendReinvested')} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                                            <label htmlFor="isStockDividendReinvested" className="text-sm text-gray-700">Reinvest Dividend?</label>
                                        </div>
                                        {isStockDividendReinvested && (
                                            <div className="p-4 border border-green-200 rounded-md bg-green-50 space-y-3">
                                                <h4 className="font-semibold text-green-800">Reinvestment Details</h4>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    <div className="form-group">
                                                        <label htmlFor="stockReinvestmentPrice" className="form-label">
                                                            Reinvestment Price {isForeignAsset && <span className="text-gray-500 text-sm">({selectedAsset.currency})</span>}
                                                        </label>
                                                        <input
                                                            id="stockReinvestmentPrice"
                                                            type="number"
                                                            step="any"
                                                            {...register('stockReinvestmentPrice', { required: "Reinvestment price is required", valueAsNumber: true, min: { value: 0.0001, message: "Must be positive" } })}
                                                            className="form-input"
                                                        />
                                                        {errors.stockReinvestmentPrice && <p className="text-red-500 text-xs italic">{errors.stockReinvestmentPrice.message}</p>}
                                                    </div>
                                                    <div className="form-group">
                                                        <label className="form-label">New Shares to be Added</label>
                                                        <div className="form-input bg-gray-100 text-gray-700">
                                                            {(dividendAmount && stockReinvestmentPrice && stockReinvestmentPrice > 0)
                                                                ? (dividendAmount / stockReinvestmentPrice).toFixed(6)
                                                                : '0.000000'}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
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

                                {/* Merger Fields */}
                                {actionType === 'MERGER' && (
                                    <div className="space-y-4">
                                        <p className="text-sm text-gray-600 dark:text-gray-400">
                                            Enter the conversion ratio and new merged company ticker. Cost basis will be preserved.
                                        </p>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="form-group">
                                                <label htmlFor="transaction_date_merger" className="form-label">Record Date</label>
                                                <input id="transaction_date_merger" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                                {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                            </div>
                                            <div className="form-group">
                                                <label htmlFor="mergerConversionRatio" className="form-label">Conversion Ratio (new:old)</label>
                                                <input id="mergerConversionRatio" type="number" step="any" {...register('mergerConversionRatio', { required: "Ratio is required", valueAsNumber: true, min: { value: 0.0001, message: "Must be positive" } })} className="form-input" placeholder="e.g., 1.68" />
                                                {errors.mergerConversionRatio && <p className="text-red-500 text-xs italic">{errors.mergerConversionRatio.message}</p>}
                                            </div>
                                        </div>
                                        <div className="form-group relative">
                                            <label htmlFor="newAssetSearch" className="form-label">New Merged Company Ticker</label>
                                            <div className="relative">
                                                <input
                                                    id="newAssetSearch"
                                                    type="text"
                                                    value={newAssetInput}
                                                    onChange={(e) => setNewAssetInput(e.target.value)}
                                                    className="form-input"
                                                    placeholder="Search for ticker..."
                                                    autoComplete="off"
                                                />
                                                {selectedNewAsset && (
                                                    <button type="button" onClick={handleClearNewAsset} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">×</button>
                                                )}
                                            </div>
                                            {isSearchingNewAsset && <p className="text-xs text-gray-500">Searching...</p>}
                                            {newAssetResults.length > 0 && (
                                                <ul className="absolute z-10 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg max-h-48 overflow-y-auto mt-1">
                                                    {newAssetResults.map((asset) => (
                                                        <li key={asset.id} onClick={() => handleSelectNewAsset(asset)} className="px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer">
                                                            <span className="font-semibold">{asset.ticker_symbol}</span> - {asset.name}
                                                        </li>
                                                    ))}
                                                </ul>
                                            )}
                                            <input type="hidden" {...register('newAssetSearch', { required: "New ticker is required" })} />
                                            {errors.newAssetSearch && <p className="text-red-500 text-xs italic">{errors.newAssetSearch.message}</p>}
                                        </div>
                                    </div>
                                )}

                                {/* Demerger Fields */}
                                {actionType === 'DEMERGER' && (
                                    <div className="space-y-4">
                                        <p className="text-sm text-gray-600 dark:text-gray-400">
                                            Enter the spin-off ratio and cost basis allocation percentage for the demerged company.
                                        </p>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="form-group">
                                                <label htmlFor="transaction_date_demerger" className="form-label">Record Date</label>
                                                <input id="transaction_date_demerger" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                                {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                            </div>
                                            <div className="form-group">
                                                <label htmlFor="demergerRatio" className="form-label">Demerger Ratio (new:old)</label>
                                                <input id="demergerRatio" type="number" step="any" {...register('demergerRatio', { required: "Ratio is required", valueAsNumber: true, min: { value: 0.0001, message: "Must be positive" } })} className="form-input" placeholder="e.g., 1" />
                                                {errors.demergerRatio && <p className="text-red-500 text-xs italic">{errors.demergerRatio.message}</p>}
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="form-group">
                                                <label htmlFor="costAllocationPct" className="form-label">Cost Allocation to Demerged (%)</label>
                                                <input id="costAllocationPct" type="number" step="any" {...register('costAllocationPct', { required: "Cost % is required", valueAsNumber: true, min: { value: 0, message: "Min 0%" }, max: { value: 100, message: "Max 100%" } })} className="form-input" placeholder="e.g., 30" />
                                                {errors.costAllocationPct && <p className="text-red-500 text-xs italic">{errors.costAllocationPct.message}</p>}
                                            </div>
                                            <div className="form-group relative">
                                                <label htmlFor="newAssetSearch_demerger" className="form-label">Demerged Company Ticker</label>
                                                <div className="relative">
                                                    <input
                                                        id="newAssetSearch_demerger"
                                                        type="text"
                                                        value={newAssetInput}
                                                        onChange={(e) => setNewAssetInput(e.target.value)}
                                                        className="form-input"
                                                        placeholder="Search for ticker..."
                                                        autoComplete="off"
                                                    />
                                                    {selectedNewAsset && (
                                                        <button type="button" onClick={handleClearNewAsset} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">×</button>
                                                    )}
                                                </div>
                                                {isSearchingNewAsset && <p className="text-xs text-gray-500">Searching...</p>}
                                                {newAssetResults.length > 0 && (
                                                    <ul className="absolute z-10 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg max-h-48 overflow-y-auto mt-1">
                                                        {newAssetResults.map((asset) => (
                                                            <li key={asset.id} onClick={() => handleSelectNewAsset(asset)} className="px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer">
                                                                <span className="font-semibold">{asset.ticker_symbol}</span> - {asset.name}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                )}
                                                <input type="hidden" {...register('newAssetSearch', { required: "New ticker is required" })} />
                                                {errors.newAssetSearch && <p className="text-red-500 text-xs italic">{errors.newAssetSearch.message}</p>}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Rename Fields */}
                                {actionType === 'RENAME' && (
                                    <div className="space-y-4">
                                        <p className="text-sm text-gray-600 dark:text-gray-400">
                                            Enter the new ticker symbol. All holdings will be transferred with preserved cost basis and holding period.
                                        </p>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="form-group">
                                                <label htmlFor="transaction_date_rename" className="form-label">Effective Date</label>
                                                <input id="transaction_date_rename" type="date" {...register('transaction_date', { required: "Date is required" })} className="form-input" />
                                                {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                                            </div>
                                            <div className="form-group relative">
                                                <label htmlFor="newAssetSearch_rename" className="form-label">New Ticker Symbol</label>
                                                <div className="relative">
                                                    <input
                                                        id="newAssetSearch_rename"
                                                        type="text"
                                                        value={newAssetInput}
                                                        onChange={(e) => setNewAssetInput(e.target.value)}
                                                        className="form-input"
                                                        placeholder="Search for ticker..."
                                                        autoComplete="off"
                                                    />
                                                    {selectedNewAsset && (
                                                        <button type="button" onClick={handleClearNewAsset} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">×</button>
                                                    )}
                                                </div>
                                                {isSearchingNewAsset && <p className="text-xs text-gray-500">Searching...</p>}
                                                {newAssetResults.length > 0 && (
                                                    <ul className="absolute z-10 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg max-h-48 overflow-y-auto mt-1">
                                                        {newAssetResults.map((asset) => (
                                                            <li key={asset.id} onClick={() => handleSelectNewAsset(asset)} className="px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer">
                                                                <span className="font-semibold">{asset.ticker_symbol}</span> - {asset.name}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                )}
                                                <input type="hidden" {...register('newAssetSearch', { required: "New ticker is required" })} />
                                                {errors.newAssetSearch && <p className="text-red-500 text-xs italic">{errors.newAssetSearch.message}</p>}
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
                                    <select id="compounding_frequency" {...register('compounding_frequency')} className="form-select">
                                        <option value="">Select...</option>
                                        <option value="Annually">Annually</option>
                                        <option value="Half-Yearly">Semi-Annually</option>
                                        <option value="Quarterly">Quarterly</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label htmlFor="interest_payout" className="form-label">Interest Payout</label>
                                    <select id="interest_payout" {...register('interest_payout')} className="form-select">
                                        <option value="">Select...</option>
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
                                disabled={Boolean(
                                    (isEditMode && (updateTransactionMutation.isPending || updateFixedDepositMutation.isPending || updateRecurringDepositMutation.isPending)) ||
                                    (!isEditMode && (createTransactionMutation.isPending || createPpfAccountMutation.isPending || createBondMutation.isPending || createFixedDepositMutation.isPending || createRecurringDepositMutation.isPending)) ||
                                    (!isEditMode && assetType === 'Stock' && !selectedAsset) ||
                                    (!isEditMode && assetType === 'Mutual Fund' && !selectedMf) ||
                                    (isForeignAsset && (isLoadingFxRate || !fxRate || isNaN(fxRate))))}
                            >
                                {isEditMode
                                    ? (updateTransactionMutation.isPending || updateFixedDepositMutation.isPending || updateRecurringDepositMutation.isPending ? 'Saving...' : 'Save Changes')
                                    : (createTransactionMutation.isPending || createPpfAccountMutation.isPending || createBondMutation.isPending || createFixedDepositMutation.isPending || createRecurringDepositMutation.isPending ? 'Saving...' : 'Save Transaction')
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

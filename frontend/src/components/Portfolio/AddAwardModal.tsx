import React, { useState, useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useQueryClient } from '@tanstack/react-query';
import { useCreateTransaction, useUpdateTransaction } from '../../hooks/usePortfolios';
import { useCreateAsset } from '../../hooks/useAssets';
import { lookupAsset, getFxRate } from '../../services/portfolioApi';
import { Asset } from '../../types/asset';
import { Transaction, TransactionCreate, TransactionUpdate } from '../../types/portfolio';
import { TransactionType } from '../../types/enums';

interface AddAwardModalProps {
    portfolioId: string;
    onClose: () => void;
    isOpen: boolean;
    transactionToEdit?: Transaction;
}

type AwardType = 'RSU_VEST' | 'ESPP_PURCHASE';

type AddAwardFormInputs = {
    awardType: AwardType;
    assetName: string; // For search input
    date: string;
    quantity: number;
    price: number; // Purchase price (0 for RSU)
    fmv: number; // FMV at vest or Market Price for ESPP

    // RSU specific
    sellToCover: boolean;
    sellQuantity?: number;
    sellPrice?: number;

    // Computed/Fetched
    fxRate: number;
};

const AddAwardModal: React.FC<AddAwardModalProps> = ({ portfolioId, onClose, isOpen, transactionToEdit }) => {
    const isEditMode = !!transactionToEdit;
    const { register, handleSubmit, control, setValue, getValues } = useForm<AddAwardFormInputs>({
        defaultValues: {
            awardType: 'RSU_VEST',
            price: 0,
            sellToCover: false,
            fxRate: 1,
        }
    });

    const queryClient = useQueryClient();
    const createTransactionMutation = useCreateTransaction();
    const updateTransactionMutation = useUpdateTransaction();
    const createAssetMutation = useCreateAsset();

    // Asset Search State
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState<Asset[]>([]);
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [isSearching, setIsSearching] = useState(false);
    const [apiError, setApiError] = useState<string | null>(null);

    const awardType = useWatch({ control, name: 'awardType' });
    const sellToCover = useWatch({ control, name: 'sellToCover' });
    const date = useWatch({ control, name: 'date' });
    const fmv = useWatch({ control, name: 'fmv' });
    const quantity = useWatch({ control, name: 'quantity' });
    const sellQuantity = useWatch({ control, name: 'sellQuantity' });
    const sellPrice = useWatch({ control, name: 'sellPrice' });

    // FX Rate
    const [isLoadingFx, setIsLoadingFx] = useState(false);

    useEffect(() => {
        if (isEditMode && transactionToEdit) {
            const details = (transactionToEdit.details || {}) as Record<string, unknown>;
            const sellToCoverDetails = (details.sell_to_cover || {}) as Record<string, unknown>;

            setValue('awardType', transactionToEdit.transaction_type as AwardType);
            setValue('date', transactionToEdit.transaction_date.split('T')[0]);
            setValue('quantity', Number(transactionToEdit.quantity));
            setValue('price', Number(transactionToEdit.price_per_unit));
            setValue('fmv', (details.fmv as number) || 0);
            setValue('fxRate', (details.fx_rate as number) || 1);

            const hasSellToCover = !!(sellToCoverDetails.quantity);
            setValue('sellToCover', hasSellToCover);
            if (hasSellToCover) {
                setValue('sellQuantity', sellToCoverDetails.quantity as number);
                setValue('sellPrice', sellToCoverDetails.price_per_unit as number);
            }

            setSelectedAsset(transactionToEdit.asset);
            setValue('assetName', transactionToEdit.asset.name);
        }
    }, [isEditMode, transactionToEdit, setValue]);

    // Search Logic
    useEffect(() => {
        const handler = setTimeout(() => {
            if (searchTerm.length >= 2 && !selectedAsset) {
                setIsSearching(true);
                lookupAsset(searchTerm, 'STOCK')
                    .then(data => setSearchResults(data))
                    .catch(() => setSearchResults([]))
                    .finally(() => setIsSearching(false));
            } else {
                setSearchResults([]);
            }
        }, 300);
        return () => clearTimeout(handler);
    }, [searchTerm, selectedAsset]);

    const handleSelectAsset = (asset: Asset) => {
        // If the asset doesn't have an ID, it's a search result from an external
        // provider and needs to be created in our database first.
        if (!asset.id) {
            createAssetMutation.mutate(
                {
                    ticker_symbol: asset.ticker_symbol,
                    name: asset.name,
                    asset_type: 'STOCK',
                    currency: asset.currency || 'USD', // Default to USD if not provided
                },
                {
                    onSuccess: (newlyCreatedAsset) => {
                        setSelectedAsset(newlyCreatedAsset);
                        setValue('assetName', newlyCreatedAsset.name);
                        setSearchTerm('');
                        setSearchResults([]);
                    },
                    onError: () => setApiError(`Failed to save asset "${asset.name}" locally.`)
                }
            );
        } else {
            // This is an asset that already exists in our DB (from a local search)
            setSelectedAsset(asset);
            setValue('assetName', asset.name);
            setSearchTerm('');
            setSearchResults([]);
        }
    };

    const handleClearAsset = () => {
        setSelectedAsset(null);
        setValue('assetName', '');
        setSearchTerm('');
    };

    const handleCreateAsset = () => {
        if (searchTerm) {
            createAssetMutation.mutate(
                {
                    ticker_symbol: searchTerm.toUpperCase(),
                    name: searchTerm,
                    asset_type: 'STOCK',
                    currency: 'USD', // Default to USD for awards usually? Or INR?
                    // Ideally we ask user or default to USD if it looks like US ticker.
                    // But for RSU/ESPP, it's often USD.
                },
                {
                    onSuccess: (newAsset) => handleSelectAsset(newAsset),
                    onError: () => setApiError(`Failed to create asset "${searchTerm}".`)
                }
            );
        }
    };

    // FX Rate Logic
    useEffect(() => {
        const handler = setTimeout(() => {
            // Check if the date is a valid YYYY-MM-DD format
            if (selectedAsset && date && /^\d{4}-\d{2}-\d{2}$/.test(date) && selectedAsset.currency && selectedAsset.currency !== 'INR') {
                setIsLoadingFx(true);
                setValue('fxRate', 1); // Reset while fetching
                getFxRate(selectedAsset.currency, 'INR', date)
                    .then(rate => setValue('fxRate', Number(rate))) // The getFxRate function returns the rate directly
                    .catch(() => setValue('fxRate', 1)) // On error, default to 1 and allow manual entry
                    .finally(() => setIsLoadingFx(false));
            }
        }, 500); // Debounce for 500ms

        return () => clearTimeout(handler);
    }, [selectedAsset, date, setValue]);

    // Defaults
    useEffect(() => {
        if (awardType === 'RSU_VEST') {
            setValue('price', 0);
        }
    }, [awardType, setValue]);

    useEffect(() => {
        if (fmv && sellToCover && !sellPrice) {
            setValue('sellPrice', fmv);
        }
    }, [fmv, sellToCover, sellPrice, setValue]);


    const onSubmit = (data: AddAwardFormInputs) => {
        if (!selectedAsset) {
            setApiError("Please select an asset.");
            return;
        }

        const payload: TransactionCreate | TransactionUpdate = {
            asset_id: selectedAsset.id,
            transaction_type: data.awardType === 'RSU_VEST' ? TransactionType.RSU_VEST : TransactionType.ESPP_PURCHASE,
            quantity: data.quantity,
            price_per_unit: data.price || 0,
            transaction_date: new Date(data.date).toISOString(),
            details: {
                fmv: data.fmv,
                fx_rate: data.fxRate,
                ...(data.awardType === 'RSU_VEST' && data.sellToCover ? {
                    sell_to_cover: {
                        quantity: data.sellQuantity,
                        price_per_unit: data.sellPrice
                    }
                } : {})
            }
        };

        const mutationOptions = {
            onSuccess: () => {
                queryClient.invalidateQueries({ queryKey: ['portfolio', portfolioId] });
                queryClient.invalidateQueries({ queryKey: ['portfolioHoldings', portfolioId] });
                queryClient.invalidateQueries({ queryKey: ['transactions'] });
                onClose();
            },
            onError: (error: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
                setApiError(error.message || `Failed to ${isEditMode ? 'update' : 'create'} transaction.`);
            }
        };

        if (isEditMode) {
            updateTransactionMutation.mutate({ portfolioId, transactionId: transactionToEdit!.id, data: payload as TransactionUpdate }, mutationOptions);
        } else {
            createTransactionMutation.mutate({ portfolioId, data: payload as TransactionCreate }, mutationOptions);
        }
    };

    if (!isOpen) return null;

    // Calculations for display
    const totalCost = (quantity || 0) * (getValues('price') || 0) * (getValues('fxRate') || 1);
    const taxableIncome = (quantity || 0) * (fmv || 0) * (getValues('fxRate') || 1);
    const netShares = (quantity || 0) - (sellToCover ? (sellQuantity || 0) : 0);

    return (
        <div className="modal-overlay z-30" onClick={onClose}>
            <div role="dialog" className="modal-content w-11/12 md:w-3/4 lg:max-w-2xl p-6 overflow-visible" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-2xl font-bold">{isEditMode ? 'Edit' : 'Add'} ESPP/RSU Award</h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    {/* Award Type Toggle */}
                    <div className="flex space-x-4 mb-4">
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="radio"
                                value="RSU_VEST"
                                {...register('awardType')}
                                disabled={isEditMode}
                                className="form-radio text-blue-600"
                            />
                            <span>RSU Vest</span>
                        </label>
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="radio"
                                value="ESPP_PURCHASE"
                                {...register('awardType')}
                                disabled={isEditMode}
                                className="form-radio text-blue-600"
                            />
                            <span>ESPP Purchase</span>
                        </label>
                    </div>

                    {/* Asset Search */}
                    <div className="form-group relative">
                        <label htmlFor="asset-search" className="form-label">Asset</label>
                        <div className="relative">
                            <input
                                id="asset-search"
                                type="text"
                                className="form-input"
                                placeholder="Search ticker (e.g. GOOGL)..."
                                value={selectedAsset ? `${selectedAsset.name} (${selectedAsset.ticker_symbol})` : searchTerm}
                                onChange={(e) => {
                                    if (selectedAsset && !isEditMode) handleClearAsset();
                                    setSearchTerm(e.target.value);
                                }}
                                disabled={!!selectedAsset || isEditMode}
                            />
                            {selectedAsset && (
                                <button
                                    type="button"
                                    onClick={handleClearAsset}
                                    className="absolute right-2 top-2 text-red-500 font-bold"
                                >
                                    &times;
                                </button>
                            )}
                        </div>
                        {/* Search Results */}
                        {!selectedAsset && searchResults.length > 0 && (
                            <ul className="absolute z-10 w-full bg-white border border-gray-300 rounded-md mt-1 max-h-40 overflow-y-auto shadow-lg">
                                {searchResults.map(asset => (
                                    <li
                                        key={asset.id}
                                        onClick={() => handleSelectAsset(asset)}
                                        className="p-2 hover:bg-gray-100 cursor-pointer"
                                    >
                                        {asset.name} ({asset.ticker_symbol})
                                    </li>
                                ))}
                            </ul>
                        )}
                        {!selectedAsset && !isSearching && searchTerm.length >= 2 && searchResults.length === 0 && (
                            <div className="absolute z-10 w-full bg-white border border-gray-300 rounded-md mt-1 p-2 shadow-lg">
                                <p className="text-sm text-gray-500 mb-2">No asset found.</p>
                                <button
                                    type="button"
                                    onClick={handleCreateAsset}
                                    className="btn btn-secondary btn-sm w-full"
                                    disabled={createAssetMutation.isPending}
                                >
                                    {createAssetMutation.isPending ? 'Creating...' : `Create Asset "${searchTerm}"`}
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="form-group">
                            <label htmlFor="date" className="form-label">{awardType === 'RSU_VEST' ? 'Vest Date' : 'Purchase Date'}</label>
                            <input id="date" type="date" {...register('date', { required: true })} className="form-input" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="quantity" className="form-label">Quantity</label>
                            <input id="quantity" type="number" step="any" {...register('quantity', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="form-group">
                            <label htmlFor="price" className="form-label">{awardType === 'RSU_VEST' ? 'Cost (0 for RSU)' : 'Purchase Price'}</label>
                            <input
                                id="price"
                                type="number"
                                step="any"
                                {...register('price', { required: true, valueAsNumber: true })}
                                className="form-input"
                                readOnly={awardType === 'RSU_VEST'}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="fmv" className="form-label">{awardType === 'RSU_VEST' ? 'FMV at Vest' : 'Market Price'}</label>
                            <input id="fmv" type="number" step="any" {...register('fmv', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                    </div>

                    {/* FX Rate Info */}
                    {selectedAsset && selectedAsset.currency !== 'INR' && (
                        <div className="p-3 bg-gray-50 rounded border border-gray-200">
                            <div className="form-group">
                                <label htmlFor="fxRate" className="form-label">FX Rate ({selectedAsset.currency}-INR)</label>
                                <input
                                    id="fxRate"
                                    type="number"
                                    step="any"
                                    {...register('fxRate', { required: true, valueAsNumber: true })}
                                    className="form-input"
                                    disabled={isLoadingFx}
                                />
                            </div>
                            {getValues('fxRate') > 1 && (
                                <div className="text-xs text-gray-600">
                                    {awardType === 'RSU_VEST'
                                        ? `Taxable Income: ₹${taxableIncome.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
                                        : `Total Cost: ₹${totalCost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
                                    }
                                </div>
                            )}
                        </div>
                    )}

                    {/* Sell to Cover (RSU Only) */}
                    {awardType === 'RSU_VEST' && (
                        <div className="border-t pt-4 mt-4">
                            <label className="flex items-center space-x-2 mb-4 cursor-pointer">
                                <input type="checkbox" {...register('sellToCover')} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                                <span className="font-semibold text-gray-700">Record 'Sell to Cover' for taxes</span>
                            </label>

                            {sellToCover && (
                                <div className="grid grid-cols-2 gap-4 pl-6 border-l-2 border-gray-200">
                                    <div className="form-group">
                                        <label htmlFor="sellQuantity" className="form-label">Shares Sold</label>
                                        <input id="sellQuantity" type="number" step="any" {...register('sellQuantity', { required: sellToCover, valueAsNumber: true })} className="form-input" />
                                    </div>
                                    <div className="form-group">
                                        <label htmlFor="sellPrice" className="form-label">Sale Price</label>
                                        <input id="sellPrice" type="number" step="any" {...register('sellPrice', { required: sellToCover, valueAsNumber: true })} className="form-input" />
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Summary */}
                    <div className="border-t pt-4 mt-4 bg-blue-50 p-4 rounded">
                        <div className="flex justify-between font-bold">
                            <span>Net Shares Received:</span>
                            <span>{netShares.toFixed(4)}</span>
                        </div>
                    </div>

                    {apiError && <div className="text-red-500 text-sm mt-2">{apiError}</div>}

                    <div className="flex justify-end space-x-4 mt-6">
                        <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                        <button type="submit" className="btn btn-primary" disabled={createTransactionMutation.isPending || updateTransactionMutation.isPending}>
                            {createTransactionMutation.isPending || updateTransactionMutation.isPending ? 'Saving...' : (isEditMode ? 'Save Changes' : 'Add Award')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddAwardModal;

import React, { useState, useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useQueryClient } from '@tanstack/react-query';
import { useCreateTransaction } from '../../hooks/usePortfolios';
import { useCreateAsset } from '../../hooks/useAssets';
import { lookupAsset, getFxRate } from '../../services/portfolioApi';
import { Asset } from '../../types/asset';
import { TransactionCreate } from '../../types/portfolio';
import { TransactionType } from '../../types/enums';

interface AddAwardModalProps {
    portfolioId: string;
    onClose: () => void;
    isOpen: boolean;
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
    fxRate?: number;
};

const AddAwardModal: React.FC<AddAwardModalProps> = ({ portfolioId, onClose, isOpen }) => {
    const { register, handleSubmit, control, setValue } = useForm<AddAwardFormInputs>({
        defaultValues: {
            awardType: 'RSU_VEST',
            price: 0,
            sellToCover: false
        }
    });

    const queryClient = useQueryClient();
    const createTransactionMutation = useCreateTransaction();
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
    const price = useWatch({ control, name: 'price' });
    const sellQuantity = useWatch({ control, name: 'sellQuantity' });
    const sellPrice = useWatch({ control, name: 'sellPrice' });

    // FX Rate State
    const [fxRate, setFxRate] = useState<number | null>(null);
    const [isLoadingFx, setIsLoadingFx] = useState(false);

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
        setSelectedAsset(asset);
        setValue('assetName', asset.name);
        setSearchTerm('');
        setSearchResults([]);
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
        if (selectedAsset && date && selectedAsset.currency && selectedAsset.currency !== 'INR') {
            setIsLoadingFx(true);
            getFxRate(selectedAsset.currency, 'INR', date)
                .then(rate => setFxRate(rate))
                .catch(() => setFxRate(null)) // Ignore error or set to 0
                .finally(() => setIsLoadingFx(false));
        } else {
            setFxRate(null);
        }
    }, [selectedAsset, date]);

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

        const payload: TransactionCreate = {
            asset_id: selectedAsset.id,
            transaction_type: data.awardType === 'RSU_VEST' ? TransactionType.RSU_VEST : TransactionType.ESPP_PURCHASE,
            quantity: data.quantity,
            price_per_unit: data.price,
            transaction_date: new Date(data.date).toISOString(),
            details: {
                fmv: data.fmv,
                fx_rate: fxRate,
                ...(data.awardType === 'RSU_VEST' && data.sellToCover ? {
                    sell_to_cover: {
                        quantity: data.sellQuantity,
                        price_per_unit: data.sellPrice
                    }
                } : {})
            }
        };

        createTransactionMutation.mutate({ portfolioId, data: payload }, {
            onSuccess: () => {
                queryClient.invalidateQueries({ queryKey: ['portfolio', portfolioId] });
                onClose();
            },
            onError: (error) => {
                setApiError(error.message || "Failed to create transaction.");
            }
        });
    };

    if (!isOpen) return null;

    // Calculations for display
    const totalCost = (quantity || 0) * (price || 0) * (fxRate || 1);
    const taxableIncome = (quantity || 0) * (fmv || 0) * (fxRate || 1);
    const netShares = (quantity || 0) - (sellToCover ? (sellQuantity || 0) : 0);

    return (
        <div className="modal-overlay z-30" onClick={onClose}>
            <div role="dialog" className="modal-content w-11/12 md:w-3/4 lg:max-w-2xl p-6 overflow-visible" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-2xl font-bold">Add ESPP/RSU Award</h2>
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
                                className="form-radio text-blue-600"
                            />
                            <span>RSU Vest</span>
                        </label>
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="radio"
                                value="ESPP_PURCHASE"
                                {...register('awardType')}
                                className="form-radio text-blue-600"
                            />
                            <span>ESPP Purchase</span>
                        </label>
                    </div>

                    {/* Asset Search */}
                    <div className="form-group relative">
                        <label className="form-label">Asset</label>
                        <div className="relative">
                            <input
                                type="text"
                                className="form-input"
                                placeholder="Search ticker (e.g. GOOGL)..."
                                value={selectedAsset ? `${selectedAsset.name} (${selectedAsset.ticker_symbol})` : searchTerm}
                                onChange={(e) => {
                                    if (selectedAsset) handleClearAsset();
                                    setSearchTerm(e.target.value);
                                }}
                                disabled={!!selectedAsset}
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
                            <label className="form-label">{awardType === 'RSU_VEST' ? 'Vest Date' : 'Purchase Date'}</label>
                            <input type="date" {...register('date', { required: true })} className="form-input" />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Quantity</label>
                            <input type="number" step="any" {...register('quantity', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="form-group">
                            <label className="form-label">{awardType === 'RSU_VEST' ? 'Cost (0 for RSU)' : 'Purchase Price'}</label>
                            <input
                                type="number"
                                step="any"
                                {...register('price', { required: true, valueAsNumber: true })}
                                className="form-input"
                                readOnly={awardType === 'RSU_VEST'}
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">{awardType === 'RSU_VEST' ? 'FMV at Vest' : 'Market Price'}</label>
                            <input type="number" step="any" {...register('fmv', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                    </div>

                    {/* FX Rate Info */}
                    {selectedAsset && selectedAsset.currency !== 'INR' && (
                        <div className="p-3 bg-gray-50 rounded border border-gray-200">
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-semibold">FX Rate ({selectedAsset.currency}-INR):</span>
                                <span className="text-sm">
                                    {isLoadingFx ? 'Fetching...' : (fxRate ? `₹${fxRate}` : 'N/A')}
                                </span>
                            </div>
                            {fxRate && (
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
                            <label className="flex items-center space-x-2 mb-4">
                                <input type="checkbox" {...register('sellToCover')} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                                <span className="font-semibold text-gray-700">Record 'Sell to Cover' for taxes</span>
                            </label>

                            {sellToCover && (
                                <div className="grid grid-cols-2 gap-4 pl-6 border-l-2 border-gray-200">
                                    <div className="form-group">
                                        <label className="form-label">Shares Sold</label>
                                        <input type="number" step="any" {...register('sellQuantity', { required: sellToCover, valueAsNumber: true })} className="form-input" />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Sale Price</label>
                                        <input type="number" step="any" {...register('sellPrice', { required: sellToCover, valueAsNumber: true })} className="form-input" />
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
                        <button type="submit" className="btn btn-primary" disabled={createTransactionMutation.isPending}>
                            {createTransactionMutation.isPending ? 'Saving...' : 'Add Award'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddAwardModal;

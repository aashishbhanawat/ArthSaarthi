import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useCreateTransaction, useCreateAsset } from '../../hooks/usePortfolios';
import { lookupAsset } from '../../services/portfolioApi';
import { Asset } from '../../types/asset';
import { TransactionCreate } from '../../types/portfolio';

interface AddTransactionModalProps {
    portfolioId: number;
    onClose: () => void;
}

const AddTransactionModal: React.FC<AddTransactionModalProps> = ({ portfolioId, onClose }) => {
    const { register, handleSubmit, setValue, formState: { errors } } = useForm<Omit<TransactionCreate, 'asset_id'>>();
    const createTransactionMutation = useCreateTransaction();
    const createAssetMutation = useCreateAsset();
    const [apiError, setApiError] = useState<string | null>(null);

    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState<Asset[]>([]);
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);

    // Debounce search term
    useEffect(() => {
        const delayDebounceFn = setTimeout(() => {
            if (searchTerm.length > 1 && !selectedAsset) {
                lookupAsset(searchTerm)
                    .then(data => setSearchResults(data))
                    .catch(() => setSearchResults([]));
            } else {
                setSearchResults([]);
            }
        }, 300);

        return () => clearTimeout(delayDebounceFn);
    }, [searchTerm, selectedAsset]);

    const handleSelectAsset = (asset: Asset) => {
        setSelectedAsset(asset);
        setSearchTerm(asset.name);
        setSearchResults([]);
    };

    const handleClearSelectedAsset = () => {
        setSelectedAsset(null);
        setSearchTerm('');
    };

    const onSubmit = (data: Omit<TransactionCreate, 'asset_id'>) => {
        if (!selectedAsset) {
            setApiError("Please select an asset.");
            return;
        }

        const payload: TransactionCreate = {
            ...data,
            asset_id: selectedAsset.id,
            quantity: Number(data.quantity),
            price_per_unit: Number(data.price_per_unit),
            fees: data.fees ? Number(data.fees) : 0,
            transaction_date: new Date(data.transaction_date).toISOString(),
        };

        createTransactionMutation.mutate({ portfolioId, data: payload }, {
            onSuccess: () => onClose(),
            onError: (error: any) => {
                const message = error.response?.data?.detail || 'An unexpected error occurred while adding the transaction';
                setApiError(message);
            }
        });
    };

    const handleCreateAsset = () => {
        setApiError(null);
        createAssetMutation.mutate(searchTerm, {
            onSuccess: (newAsset) => {
                handleSelectAsset(newAsset);
            },
            onError: (error: any) => {
                setApiError(error.response?.data?.detail || 'Failed to create asset.');
            }
        });
    };

    return (
        <div className="modal-overlay z-30">
            <div className="modal-content overflow-visible w-11/12 md:w-3/4 lg:max-w-2xl p-6">
                <h2 className="text-2xl font-bold mb-4">Add Transaction</h2>
                <div className="max-h-[70vh] overflow-y-auto px-2 -mr-2">
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        {/* Asset Search */}
                        <div className="form-group">
                            <label htmlFor="asset-search" className="form-label">Asset</label>
                            <div className="relative">
                                <input
                                    type="text"
                                    id="asset-search"
                                    className="form-input"
                                    value={searchTerm}
                                    onChange={(e) => {
                                        setApiError(null);
                                        if (selectedAsset) handleClearSelectedAsset();
                                        setSearchTerm(e.target.value);
                                    }}
                                    placeholder="Search by ticker or name..."
                                    autoComplete="off"
                                />
                                {selectedAsset && (
                                    <button type="button" onClick={handleClearSelectedAsset} className="absolute right-2 top-2 text-red-500 text-xl font-bold">
                                        &times;
                                    </button>
                                )}
                                {searchResults.length > 0 && !selectedAsset && (
                                    <ul className="absolute z-20 w-full bg-white border border-gray-300 rounded-md mt-1 max-h-40 overflow-y-auto shadow-lg">
                                        {searchResults.map(asset => (
                                            <li key={asset.id} onClick={() => handleSelectAsset(asset)} className="p-2 hover:bg-gray-100 cursor-pointer">
                                                {asset.name} ({asset.ticker_symbol})
                                            </li>
                                        ))}
                                    </ul>
                                )}
                                {searchResults.length === 0 && searchTerm.length > 1 && !selectedAsset && (
                                    <div className="absolute z-20 w-full bg-white border border-gray-300 rounded-md mt-1 p-2 shadow-lg">
                                        <p className="text-sm text-gray-500 mb-2">No asset found. You can create it.</p>
                                        <button type="button" onClick={handleCreateAsset} className="btn btn-secondary btn-sm w-full" disabled={createAssetMutation.isPending}>
                                            {createAssetMutation.isPending ? 'Creating...' : `Create Asset "${searchTerm.toUpperCase()}"`}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Transaction Details */}
                        <div className="grid grid-cols-2 gap-4 pt-4">
                            <div className="form-group">
                                <label htmlFor="transaction_type" className="form-label">Type</label>
                                <select id="transaction_type" {...register('transaction_type')} className="form-input">
                                    <option value="BUY">Buy</option>
                                    <option value="SELL">Sell</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label htmlFor="quantity" className="form-label">Quantity</label>
                                <input id="quantity" type="number" step="any" {...register('quantity', { required: true, valueAsNumber: true })} className="form-input" />
                            </div>
                            <div className="form-group">
                                <label htmlFor="price_per_unit" className="form-label">Price per Unit</label>
                                <input id="price_per_unit" type="number" step="any" {...register('price_per_unit', { required: true, valueAsNumber: true })} className="form-input" />
                            </div>
                            <div className="form-group">
                                <label htmlFor="transaction_date" className="form-label">Date</label>
                                <input id="transaction_date" type="date" {...register('transaction_date', { required: true })} className="form-input" />
                            </div>
                            <div className="form-group col-span-2">
                                <label htmlFor="fees" className="form-label">Fees (optional)</label>
                                <input id="fees" type="number" step="any" {...register('fees', { valueAsNumber: true })} className="form-input" />
                            </div>
                        </div>

                        {apiError && <p className="text-red-500 text-sm mt-2">{apiError}</p>}

                        <div className="flex justify-end space-x-4 pt-4">
                            <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                            <button type="submit" className="btn btn-primary" disabled={createTransactionMutation.isPending || !selectedAsset}>
                                {createTransactionMutation.isPending ? 'Saving...' : 'Save Transaction'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default AddTransactionModal;

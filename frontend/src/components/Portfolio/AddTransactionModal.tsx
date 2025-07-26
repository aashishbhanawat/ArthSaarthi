import React, { useState, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { useLookupAsset, useCreateTransaction } from '../../hooks/usePortfolios';
import { Asset, TransactionCreate, NewAsset } from '../../types/portfolio';
import axios from 'axios';

interface AddTransactionModalProps {
    isOpen: boolean;
    onClose: () => void;
    portfolioId: number;
}

type FormInputs = {
    ticker_symbol: string;
    name: string;
    asset_type: string;
    currency: string;
    transaction_type: 'BUY' | 'SELL';
    quantity: number;
    price_per_unit: number;
    transaction_date: string;
    fees?: number;
};

const AddTransactionModal: React.FC<AddTransactionModalProps> = ({ isOpen, onClose, portfolioId }) => {
    const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm<FormInputs>();
    const [foundAsset, setFoundAsset] = useState<Asset | null>(null);
    const [apiError, setApiError] = useState<string | null>(null);
    const [isManualEntry, setIsManualEntry] = useState(false);

    const lookupAssetMutation = useLookupAsset();
    const createTransactionMutation = useCreateTransaction();

    const tickerValue = watch('ticker_symbol');

    useEffect(() => {
        if (createTransactionMutation.isSuccess) {
            setApiError(null);
            reset();
            setFoundAsset(null);
            setIsManualEntry(false);
            onClose();
            createTransactionMutation.reset();
        }
    }, [createTransactionMutation.isSuccess, onClose, reset]);

    const handleTickerBlur = async () => {
        if (tickerValue) {
            try {
                const asset = await lookupAssetMutation.mutateAsync(tickerValue.toUpperCase());
                setFoundAsset(asset);
                setValue('name', asset.name);
                setValue('asset_type', asset.asset_type);
                setValue('currency', asset.currency);
                setIsManualEntry(false);
            } catch (error) {
                setFoundAsset(null);
                setIsManualEntry(true);
            }
        }
    };

    const onSubmit: SubmitHandler<FormInputs> = (data) => {
        setApiError(null);
        const transactionData: TransactionCreate = {
            transaction_type: data.transaction_type,
            quantity: data.quantity,
            price_per_unit: data.price_per_unit,
            transaction_date: new Date(data.transaction_date).toISOString(),
            fees: data.fees || 0,
        };

        if (foundAsset) {
            transactionData.asset_id = foundAsset.id;
        } else {
            const newAsset: NewAsset = {
                ticker_symbol: data.ticker_symbol.toUpperCase(),
                name: data.name,
                asset_type: data.asset_type,
                currency: data.currency.toUpperCase(),
            };
            transactionData.new_asset = newAsset;
        }
        createTransactionMutation.mutate({ portfolioId, data: transactionData }, {
            onError: (error) => {
                if (axios.isAxiosError(error) && error.response?.data?.detail) {
                    setApiError(error.response.data.detail);
                } else {
                    setApiError('An unexpected error occurred while adding the transaction.');
                }
            },
        });
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content max-w-lg">
                <div className="modal-header">
                    <h2 className="text-2xl font-bold">Add New Transaction</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
                </div>
                <div className="p-6">
                    <form onSubmit={handleSubmit(onSubmit)} noValidate>
                        {/* Ticker Symbol */}
                        <div className="form-group">
                            <label htmlFor="ticker_symbol" className="form-label">Ticker Symbol</label>
                            <input
                                id="ticker_symbol"
                                {...register('ticker_symbol', { required: 'Ticker is required' })}
                                onBlur={handleTickerBlur}
                                className="form-input"
                                disabled={lookupAssetMutation.isPending}
                            />
                            {lookupAssetMutation.isPending && <p className="text-sm text-blue-500">Looking up asset...</p>}
                            {errors.ticker_symbol && <p className="text-red-500 text-xs italic">{errors.ticker_symbol.message}</p>}
                        </div>

                        {/* Asset Details */}
                        {(foundAsset || isManualEntry) && (
                            <>
                                <div className="form-group">
                                    <label htmlFor="name" className="form-label">Asset Name</label>
                                    <input id="name" {...register('name', { required: 'Name is required' })} className="form-input" disabled={!isManualEntry} />
                                    {errors.name && <p className="text-red-500 text-xs italic">{errors.name.message}</p>}
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label htmlFor="asset_type" className="form-label">Asset Type</label>
                                        <input id="asset_type" {...register('asset_type', { required: 'Type is required' })} className="form-input" disabled={!isManualEntry} />
                                        {errors.asset_type && <p className="text-red-500 text-xs italic">{errors.asset_type.message}</p>}
                                    </div>
                                    <div>
                                        <label htmlFor="currency" className="form-label">Currency</label>
                                        <input id="currency" {...register('currency', { required: 'Currency is required' })} className="form-input" disabled={!isManualEntry} />
                                        {errors.currency && <p className="text-red-500 text-xs italic">{errors.currency.message}</p>}
                                    </div>
                                </div>
                                {isManualEntry && <p className="text-sm text-yellow-600 bg-yellow-100 p-2 rounded mt-4">Asset not found. Please enter details manually.</p>}
                            </>
                        )}

                        {/* Transaction Details */}
                        <div className="grid grid-cols-2 gap-4 form-group">
                            <div>
                                <label htmlFor="transaction_type" className="form-label">Type</label>
                                <select id="transaction_type" {...register('transaction_type', { required: true })} className="form-input">
                                    <option value="BUY">BUY</option>
                                    <option value="SELL">SELL</option>
                                </select>
                            </div>
                            <div>
                                <label htmlFor="transaction_date" className="form-label">Date</label>
                                <input type="date" id="transaction_date" {...register('transaction_date', { required: 'Date is required' })} className="form-input" />
                                {errors.transaction_date && <p className="text-red-500 text-xs italic">{errors.transaction_date.message}</p>}
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4 form-group">
                            <div>
                                <label htmlFor="quantity" className="form-label">Quantity</label>
                                <input type="number" step="any" id="quantity" {...register('quantity', { required: 'Quantity is required', valueAsNumber: true, min: { value: 0, message: "Must be positive" } })} className="form-input" />
                                {errors.quantity && <p className="text-red-500 text-xs italic">{errors.quantity.message}</p>}
                            </div>
                            <div>
                                <label htmlFor="price_per_unit" className="form-label">Price/Unit</label>
                                <input type="number" step="any" id="price_per_unit" {...register('price_per_unit', { required: 'Price is required', valueAsNumber: true, min: { value: 0, message: "Must be positive" } })} className="form-input" />
                                {errors.price_per_unit && <p className="text-red-500 text-xs italic">{errors.price_per_unit.message}</p>}
                            </div>
                            <div>
                                <label htmlFor="fees" className="form-label">Fees</label>
                                <input type="number" step="any" id="fees" {...register('fees', { valueAsNumber: true, min: { value: 0, message: "Must be positive" } })} className="form-input" />
                                {errors.fees && <p className="text-red-500 text-xs italic">{errors.fees.message}</p>}
                            </div>
                        </div>

                        {apiError && (
                            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                                <span className="block sm:inline">{apiError}</span>
                            </div>
                        )}

                        <div className="flex items-center justify-end pt-4">
                            <button type="button" onClick={onClose} className="btn btn-secondary mr-2" disabled={createTransactionMutation.isPending || lookupAssetMutation.isPending}>
                                Cancel
                            </button>
                            <button type="submit" className="btn btn-primary" disabled={createTransactionMutation.isPending}>
                                {createTransactionMutation.isPending ? 'Adding...' : 'Add Transaction'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default AddTransactionModal;
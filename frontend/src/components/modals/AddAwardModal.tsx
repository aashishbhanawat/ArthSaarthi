
import React, { useState, useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { useCreateTransaction } from '~/hooks/usePortfolios';
import { useAssetsByType } from '~/hooks/useAssets';
import { getFxRate } from '~/services/fxRateApi';
import { Asset } from '~/types/asset';
import { TransactionCreate } from '~/types/portfolio';
import Select from 'react-select';

interface AddAwardModalProps {
  portfolioId: string;
  onClose: () => void;
  isOpen: boolean;
}

type AwardFormInputs = {
  award_type: 'RSU' | 'ESPP';
  asset_id: string;
  vest_date?: string;
  gross_qty_vested?: number;
  fmv_at_vest?: number;
  record_sell_to_cover?: boolean;
  shares_sold?: number;
  sale_price?: number;
  purchase_date?: string;
  quantity?: number;
  purchase_price?: number;
  market_price?: number;
  fx_rate?: number;
};

const AddAwardModal: React.FC<AddAwardModalProps> = ({ portfolioId, onClose, isOpen }) => {
  const { register, handleSubmit, control, setValue, watch } = useForm<AwardFormInputs>({
    defaultValues: { award_type: 'RSU' }
  });
  const queryClient = useQueryClient();
  const createTransactionMutation = useCreateTransaction();
  const [apiError, setApiError] = useState<string | null>(null);

  const awardType = useWatch({ control, name: 'award_type' });
  const recordSellToCover = useWatch({ control, name: 'record_sell_to_cover' });
  const vestDate = useWatch({ control, name: 'vest_date' });

  const { data: stockAssets, isLoading: isLoadingStockAssets } = useAssetsByType(
    portfolioId,
    'STOCK',
    {
      enabled: isOpen,
    }
  );

  const { data: fxRate, isError: isFxRateError } = useQuery({
    queryKey: ['fxRate', vestDate],
    queryFn: () => getFxRate('USD', 'INR', vestDate!),
    enabled: !!vestDate,
  });

  useEffect(() => {
    if (fxRate) {
      setValue('fx_rate', fxRate.rate);
    }
  }, [fxRate, setValue]);

  const watchedFields = watch();
  const taxableIncome = (watchedFields.gross_qty_vested || 0) * (watchedFields.fmv_at_vest || 0) * (watchedFields.fx_rate || 0);
  const netSharesReceived = (watchedFields.gross_qty_vested || 0) - (watchedFields.shares_sold || 0);

  const onSubmit = () => {
    const data = watch();
    const commonPayload = {
        asset_id: data.asset_id,
        fees: 0,
    };

    let payload: TransactionCreate | TransactionCreate[];

    if (data.award_type === 'RSU') {
        const details: Record<string, unknown> = {
            fmv_at_vest: data.fmv_at_vest!,
            exchange_rate_to_inr: data.fx_rate!,
            grant_date: '', // This can be added as a new form field if needed
        };

        if (data.record_sell_to_cover && data.shares_sold! > 0) {
            details.sell_to_cover_shares = data.shares_sold!;
            details.sell_to_cover_price = data.sale_price!;
        }

        payload = {
            ...commonPayload,
            transaction_type: 'RSU_VEST',
            quantity: data.gross_qty_vested!,
            price_per_unit: 0,
            transaction_date: new Date(data.vest_date!).toISOString(),
            details: details,
        };
    } else {
        payload = {
            ...commonPayload,
            transaction_type: 'ESPP_PURCHASE',
            quantity: data.quantity!,
            price_per_unit: data.purchase_price!,
            transaction_date: new Date(data.purchase_date!).toISOString(),
            details: {
                market_price: data.market_price!,
                discount_percentage: ((data.market_price! - data.purchase_price!) / data.market_price!) * 100,
                exchange_rate_to_inr: data.fx_rate!,
                offering_begin_date: '',
            },
        };
    }

    createTransactionMutation.mutate({ portfolioId, data: payload }, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['portfolio', portfolioId] });
        onClose();
      },
      onError: (error: { response?: { data?: { detail?: string } } }) => {
        setApiError(error.response?.data?.detail || 'An error occurred.');
      }
    });
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay z-30" onClick={onClose}>
      <div role="dialog" aria-modal="true" className="modal-content overflow-visible w-11/12 md:w-3/4 lg:max-w-2xl p-6" onClick={e => e.stopPropagation()}>
        <h2 className="text-2xl font-bold mb-4">Add ESPP/RSU Award</h2>
        <div className="max-h-[70vh] overflow-y-auto px-2 -mr-2">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="form-group">
              <label className="form-label">Award Type</label>
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input type="radio" value="RSU" {...register('award_type')} className="form-radio" />
                  <span className="ml-2">RSU Vest</span>
                </label>
                <label className="flex items-center">
                  <input type="radio" value="ESPP" {...register('award_type')} className="form-radio" />
                  <span className="ml-2">ESPP Purchase</span>
                </label>
              </div>
            </div>

            <div className="form-group">
                <label htmlFor="asset-select" className="form-label">Asset</label>
                <Select
                    inputId="asset-select"
                    options={stockAssets}
                    isLoading={isLoadingStockAssets}
                    getOptionLabel={(option: Asset) => `${option.name} (${option.ticker_symbol})`}
                    getOptionValue={(option: Asset) => option.id}
                    onChange={(option) => setValue('asset_id', option?.id || '')}
                    isClearable
                    placeholder="Select a stock..."
                />
            </div>

            {awardType === 'RSU' && (
              <div className="space-y-4 p-4 border border-gray-200 rounded-md bg-gray-50/50">
                <div className="grid grid-cols-2 gap-4">
                    <div className="form-group">
                        <label htmlFor="vest_date" className="form-label">Vest Date</label>
                        <input id="vest_date" type="date" {...register('vest_date', { required: true })} className="form-input" />
                    </div>
                    <div className="form-group">
                        <label htmlFor="gross_qty_vested" className="form-label">Gross Qty Vested</label>
                        <input id="gross_qty_vested" type="number" step="any" {...register('gross_qty_vested', { required: true, valueAsNumber: true })} className="form-input" />
                    </div>
                    <div className="form-group">
                        <label htmlFor="fmv_at_vest" className="form-label">FMV at Vest (USD)</label>
                        <input id="fmv_at_vest" type="number" step="any" {...register('fmv_at_vest', { required: true, valueAsNumber: true })} className="form-input" />
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div className="form-group">
                        <label htmlFor="fx_rate" className="form-label">FX Rate (USD-INR)</label>
                        <input id="fx_rate" type="number" step="any" {...register('fx_rate', { required: true, valueAsNumber: true })} className="form-input" readOnly={!isFxRateError} />
                        {isFxRateError && <p className="text-xs text-gray-500">Could not fetch rate. Please enter manually.</p>}
                    </div>
                    <div className="form-group">
                        <label className="form-label">Taxable Income (INR)</label>
                        <input type="text" value={`₹${taxableIncome.toFixed(2)}`} readOnly className="form-input bg-gray-100" />
                    </div>
                </div>
                <div className="flex items-center space-x-2">
                    <input id="record_sell_to_cover" type="checkbox" {...register('record_sell_to_cover')} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                    <label htmlFor="record_sell_to_cover" className="text-sm text-gray-700">Record 'Sell to Cover' for taxes</label>
                </div>
                {recordSellToCover && (
                    <div className="grid grid-cols-2 gap-4">
                        <div className="form-group">
                            <label htmlFor="shares_sold" className="form-label">Shares Sold</label>
                            <input id="shares_sold" type="number" step="any" {...register('shares_sold', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="sale_price" className="form-label">Sale Price (USD)</label>
                            <input id="sale_price" type="number" step="any" {...register('sale_price', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Net Shares Received</label>
                            <input type="text" value={netSharesReceived} readOnly className="form-input bg-gray-100" />
                        </div>
                    </div>
                )}
              </div>
            )}

            {awardType === 'ESPP' && (
                <div className="space-y-4 p-4 border border-gray-200 rounded-md bg-gray-50/50">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="form-group">
                            <label htmlFor="purchase_date" className="form-label">Purchase Date</label>
                            <input id="purchase_date" type="date" {...register('purchase_date', { required: true })} className="form-input" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="quantity" className="form-label">Quantity</label>
                            <input id="quantity" type="number" step="any" {...register('quantity', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="purchase_price" className="form-label">Purchase Price (USD)</label>
                            <input id="purchase_price" type="number" step="any" {...register('purchase_price', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="market_price" className="form-label">Market Price (USD)</label>
                            <input id="market_price" type="number" step="any" {...register('market_price', { required: true, valueAsNumber: true })} className="form-input" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="fx_rate" className="form-label">FX Rate (USD-INR)</label>
                            <input id="fx_rate" type="number" step="any" {...register('fx_rate', { required: true, valueAsNumber: true })} className="form-input" readOnly={!isFxRateError} />
                            {isFxRateError && <p className="text-xs text-gray-500">Could not fetch rate. Please enter manually.</p>}
                        </div>
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
                <button type="submit" className="btn btn-primary" disabled={createTransactionMutation.isPending}>
                    {createTransactionMutation.isPending ? 'Saving...' : 'Add Award'}
                </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AddAwardModal;

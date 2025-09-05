import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useCreateTransaction } from '../../hooks/useTransactions';
import { useCreateFixedDeposit } from '../../hooks/usePortfolios';
import { Asset } from '../../types/asset';

interface TransactionFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    portfolioId: string;
    assets: Asset[];
}

interface TransactionFormData {
    assetId: string;
    transactionType: 'BUY' | 'SELL';
    quantity: string;
    price: string;
    transactionDate: string;
    institutionName: string;
    accountNumber: string;
    principalAmount: string;
    interestRate: string;
    startDate: string;
    maturityDate: string;
}

const TransactionFormModal: React.FC<TransactionFormModalProps> = ({ isOpen, onClose, portfolioId, assets }) => {
    const { register, handleSubmit, reset } = useForm<TransactionFormData>();
    const createTransaction = useCreateTransaction();
    const createFixedDeposit = useCreateFixedDeposit();
    const [selectedAssetType, setSelectedAssetType] = useState('Stock');

    const onSubmit = async (data: TransactionFormData) => {
        if (selectedAssetType === 'Fixed Deposit') {
            await createFixedDeposit.mutateAsync({
                portfolioId: portfolioId,
                name: data.institutionName,
                account_number: data.accountNumber,
                principal_amount: parseFloat(data.principalAmount),
                interest_rate: parseFloat(data.interestRate),
                start_date: data.startDate,
                maturity_date: data.maturityDate,
                compounding_frequency: 'Annually', // This can be a form field later
                interest_payout: 'Cumulative', // This can be a form field later
            });
        } else {
            await createTransaction.mutateAsync({
                portfolio_id: portfolioId,
                asset_id: data.assetId,
                transaction_type: data.transactionType,
                quantity: parseFloat(data.quantity),
                price_per_unit: parseFloat(data.price),
                transaction_date: data.transactionDate,
            });
        }
        reset();
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full" id="my-modal">
            <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
                <div className="mt-3 text-center">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">Add New Transaction</h3>
                    <form onSubmit={handleSubmit(onSubmit)} className="mt-2">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="asset-type" className="block text-sm font-medium text-gray-700">Asset Type</label>
                                <select id="asset-type" onChange={(e) => setSelectedAssetType(e.target.value)} value={selectedAssetType} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
                                    <option>Stock</option>
                                    <option>Mutual Fund</option>
                                    <option>ETF</option>
                                    <option>Fixed Deposit</option>
                                    <option>Bond</option>
                                </select>
                            </div>

                            {selectedAssetType !== 'Fixed Deposit' && (
                                <>
                                    <div>
                                        <label htmlFor="assetId" className="block text-sm font-medium text-gray-700">Asset</label>
                                        <select id="assetId" {...register('assetId')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
                                            {assets.filter(a => a.asset_type === selectedAssetType).map(asset => (
                                                <option key={asset.id} value={asset.id}>{asset.name} ({asset.ticker_symbol})</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label htmlFor="transactionType" className="block text-sm font-medium text-gray-700">Transaction Type</label>
                                        <select id="transactionType" {...register('transactionType')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
                                            <option>BUY</option>
                                            <option>SELL</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label htmlFor="quantity" className="block text-sm font-medium text-gray-700">Quantity</label>
                                        <input type="number" step="any" id="quantity" {...register('quantity')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                                    </div>
                                    <div>
                                        <label htmlFor="price" className="block text-sm font-medium text-gray-700">Price per Unit</label>
                                        <input type="number" step="any" id="price" {...register('price')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                                    </div>
                                    <div>
                                        <label htmlFor="transactionDate" className="block text-sm font-medium text-gray-700">Transaction Date</label>
                                        <input type="date" id="transactionDate" {...register('transactionDate')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                                    </div>
                                </>
                            )}

                            {selectedAssetType === 'Fixed Deposit' && (
                                <>
                                    <div className="col-span-2">
                                        <label htmlFor="institution-name" className="block text-sm font-medium text-gray-700">Institution Name</label>
                                        <input type="text" id="institution-name" {...register('institutionName')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                                    </div>
                                    <div className="col-span-2">
                                        <label htmlFor="account-number" className="block text-sm font-medium text-gray-700">FD Account Number</label>
                                        <input type="text" id="account-number" {...register('accountNumber')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                                    </div>
                                    <div className="col-span-1">
                                        <label htmlFor="principal-amount" className="block text-sm font-medium text-gray-700">Principal Amount</label>
                                        <input type="number" id="principal-amount" {...register('principalAmount')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                                    </div>
                                    <div className="col-span-1">
                                        <label htmlFor="interest-rate" className="block text-sm font-medium text-gray-700">Interest Rate (%)</label>
                                        <input type="number" id="interest-rate" {...register('interestRate')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                                    </div>
                                    <div>
                                        <label htmlFor="start-date" className="block text-sm font-medium text-gray-700">Start Date</label>
                                        <input type="date" id="start-date" {...register('startDate')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                                    </div>
                                    <div>
                                        <label htmlFor="maturity-date" className="block text-sm font-medium text-gray-700">Maturity Date</label>
                                        <input type="date" id="maturity-date" {...register('maturityDate')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
                                    </div>
                                </>
                            )}
                        </div>

                        <div className="items-center gap-2 mt-3 sm:flex">
                            <button type="submit" className="w-full mt-2 p-2.5 flex-1 text-white bg-indigo-600 rounded-md outline-none ring-offset-2 ring-indigo-600 focus:ring-2">
                                Add Transaction
                            </button>
                            <button type="button" onClick={onClose} className="w-full mt-2 p-2.5 flex-1 text-gray-800 rounded-md outline-none border ring-offset-2 ring-indigo-600 focus:ring-2">
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default TransactionFormModal;
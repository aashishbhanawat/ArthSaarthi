import React from 'react';
import { DividendEntry } from '../../hooks/useDividends';
import { usePrivacy } from '../../context/PrivacyContext';

interface DividendCardProps {
    entry: DividendEntry;
}

const DividendCard: React.FC<DividendCardProps> = ({ entry }) => {
    const { isPrivacyMode } = usePrivacy();

    const formatVal = (val: number, currency: string = 'INR') => {
        if (isPrivacyMode) return currency === 'INR' ? '₹ ••••••' : `${currency} ••••••`;
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency,
            maximumFractionDigits: 2,
        }).format(val);
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-4">
            <div className="flex justify-between items-start mb-3">
                <div className="flex flex-col">
                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100">{entry.asset_name || entry.asset_ticker}</span>
                    <span className="text-[10px] text-gray-400 font-mono uppercase">{entry.asset_ticker}</span>
                </div>
                <div className="text-right">
                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400 font-mono">
                        {new Date(entry.date).toLocaleDateString('en-IN')}
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 py-3 border-t border-b border-gray-50 dark:border-gray-700">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Quantity</span>
                    <span className="text-xs font-medium dark:text-gray-300">{Number(entry.quantity).toLocaleString(undefined, { maximumFractionDigits: 4 })}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Amount (Native)</span>
                    <span className="text-xs font-medium dark:text-gray-300">{formatVal(entry.amount_native, entry.currency)}</span>
                </div>
            </div>

            {entry.currency !== 'INR' && entry.ttbr_rate && (
                <div className="mt-2 py-2 px-3 bg-gray-50 dark:bg-gray-900/40 rounded-lg flex justify-between items-center">
                    <div className="flex flex-col">
                        <span className="text-[9px] text-gray-400 uppercase">TTBR Rate</span>
                        <span className="text-[10px] font-medium dark:text-gray-300">₹{entry.ttbr_rate.toFixed(4)}</span>
                    </div>
                    <div className="text-right flex flex-col">
                        <span className="text-[9px] text-gray-400 uppercase">TTBR Date</span>
                        <span className="text-[10px] font-medium dark:text-gray-300">{entry.ttbr_date ? new Date(entry.ttbr_date).toLocaleDateString('en-IN') : '-'}</span>
                    </div>
                </div>
            )}

            <div className="mt-3 pt-3 flex justify-between items-center">
                <span className="text-xs font-bold text-gray-600 dark:text-gray-400">Net Dividend (INR)</span>
                <span className="text-sm font-extrabold text-green-600 dark:text-green-400">
                    {formatVal(entry.amount_inr, 'INR')}
                </span>
            </div>
        </div>
    );
};

export default DividendCard;

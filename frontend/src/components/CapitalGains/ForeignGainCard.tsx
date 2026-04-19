import React from 'react';
import { ForeignGainEntry } from '../../hooks/useCapitalGains';
import { usePrivacy } from '../../context/PrivacyContext';

interface ForeignGainCardProps {
    gain: ForeignGainEntry;
}

const ForeignGainCard: React.FC<ForeignGainCardProps> = ({ gain }) => {
    const { isPrivacyMode } = usePrivacy();

    const formatVal = (val: number, currency: string) => {
        if (isPrivacyMode) return `${currency} ••••••`;
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency,
            maximumFractionDigits: 2,
        }).format(val);
    };

    const isProfit = gain.gain >= 0;

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-4">
            <div className="flex justify-between items-start mb-3">
                <div className="flex flex-col">
                    <div className="flex items-center gap-1">
                        <span className="text-sm font-bold text-gray-900 dark:text-gray-100">{gain.asset_name || gain.asset_ticker}</span>
                        {gain.country_code && (
                            <span className="text-[9px] bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-1 rounded uppercase tracking-tighter">{gain.country_code}</span>
                        )}
                    </div>
                    <span className="text-[10px] text-gray-400 font-mono uppercase">{gain.asset_ticker}</span>
                </div>
                <div className="text-right flex flex-col items-end">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${gain.gain_type === 'LTCG'
                        ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                        : 'bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                        }`}>
                        {gain.gain_type}
                    </span>
                    <span className="text-[10px] text-gray-500 mt-1 font-mono uppercase">{gain.currency}</span>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-y-3 gap-x-4 py-3 border-t border-b border-gray-50 dark:border-gray-700 font-mono">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-sans font-bold">Quantity</span>
                    <span className="text-xs font-medium dark:text-gray-300">{Number(gain.quantity).toLocaleString(undefined, { maximumFractionDigits: 4 })}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-sans font-bold">Holding Days</span>
                    <span className="text-xs font-medium dark:text-gray-300">{gain.holding_days} Days</span>
                </div>
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-sans font-bold">Buy Date</span>
                    <span className="text-xs font-medium dark:text-gray-300">{new Date(gain.buy_date).toLocaleDateString('en-IN')}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-sans font-bold">Sell Date</span>
                    <span className="text-xs font-medium dark:text-gray-300">{new Date(gain.sell_date).toLocaleDateString('en-IN')}</span>
                </div>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-4">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Buy Value</span>
                    <span className="text-sm font-semibold dark:text-gray-200">{formatVal(gain.total_buy_value, gain.currency)}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Sell Value</span>
                    <span className="text-sm font-semibold dark:text-gray-200">{formatVal(gain.total_sell_value, gain.currency)}</span>
                </div>
            </div>

            <div className="mt-3 pt-3 border-t border-gray-50 dark:border-gray-700 flex justify-between items-center">
                <span className="text-xs font-bold text-gray-600 dark:text-gray-400 uppercase tracking-tighter">Gain/Loss ({gain.currency})</span>
                <span className={`text-sm font-extrabold ${isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {formatVal(gain.gain, gain.currency)}
                </span>
            </div>
        </div>
    );
};

export default ForeignGainCard;

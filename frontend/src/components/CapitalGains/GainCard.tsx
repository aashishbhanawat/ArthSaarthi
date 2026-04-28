import React from 'react';
import { GainEntry } from '../../hooks/useCapitalGains';
import { formatCurrency } from '../../utils/formatting';
import { usePrivacy } from '../../context/PrivacyContext';

interface GainCardProps {
    gain: GainEntry;
}

const GainCard: React.FC<GainCardProps> = ({ gain }) => {
    const { isPrivacyMode } = usePrivacy();

    const formatVal = (val: number) => {
        if (isPrivacyMode) return '₹ ••••••';
        return formatCurrency(val, 'INR');
    };

    const isProfit = gain.gain >= 0;

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-4 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-3">
                <div className="flex flex-col">
                    <div className="flex items-center gap-1">
                        <span className="text-sm font-bold text-gray-900 dark:text-gray-100">{gain.asset_name || gain.asset_ticker}</span>
                        {gain.is_hybrid_warning && (
                            <span title="Hybrid Fund: Tax rate depends on equity exposure. Verify manually." className="cursor-help text-yellow-500 text-xs">⚠️</span>
                        )}
                    </div>
                    <span className="text-[10px] text-gray-400 font-mono uppercase">{gain.asset_ticker}</span>
                </div>
                <div className="text-right flex flex-col items-end">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${gain.gain_type === 'LTCG'
                            ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                            : 'bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                        }`}>
                        {gain.tax_rate}
                    </span>
                    <span className="text-[10px] text-gray-500 mt-1">{gain.asset_type}</span>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-y-3 gap-x-4 py-3 border-t border-b border-gray-50 dark:border-gray-700">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Quantity</span>
                    <span className="text-xs font-medium dark:text-gray-300">{Number(gain.quantity).toLocaleString(undefined, { maximumFractionDigits: 4 })}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Holding Days</span>
                    <span className="text-xs font-medium dark:text-gray-300">{gain.holding_days} Days</span>
                </div>
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Buy Date</span>
                    <span className="text-xs font-medium dark:text-gray-300 font-mono">{new Date(gain.buy_date).toLocaleDateString('en-IN')}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Sell Date</span>
                    <span className="text-xs font-medium dark:text-gray-300 font-mono">{new Date(gain.sell_date).toLocaleDateString('en-IN')}</span>
                </div>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-4">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Buy Value</span>
                    <span className="text-sm font-semibold dark:text-gray-200">{formatVal(gain.total_buy_value)}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Sell Value</span>
                    <span className="text-sm font-semibold dark:text-gray-200">{formatVal(gain.total_sell_value)}</span>
                </div>
            </div>

            <div className="mt-3 pt-3 border-t border-gray-50 dark:border-gray-700 flex justify-between items-center">
                <span className="text-xs font-bold text-gray-600 dark:text-gray-400">Realized Gain</span>
                <span className={`text-sm font-extrabold ${isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {formatVal(gain.gain)}
                </span>
            </div>

            {(gain.is_grandfathered || gain.corporate_action_adjusted) && (
                <div className="mt-2 flex gap-2">
                    {gain.is_grandfathered && <span className="text-[9px] bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded font-bold uppercase tracking-tighter">Grandfathered</span>}
                    {gain.corporate_action_adjusted && <span className="text-[9px] bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 px-1.5 py-0.5 rounded font-bold uppercase tracking-tighter">CA Adjusted</span>}
                </div>
            )}
        </div>
    );
};

export default GainCard;

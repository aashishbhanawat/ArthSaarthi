import React from 'react';
import { Schedule112AEntry } from '../../hooks/useCapitalGains';
import { formatCurrency } from '../../utils/formatting';
import { usePrivacy } from '../../context/PrivacyContext';

interface Gain112ACardProps {
    entry: Schedule112AEntry;
}

const Gain112ACard: React.FC<Gain112ACardProps> = ({ entry }) => {
    const { isPrivacyMode } = usePrivacy();

    const formatVal = (val: number | null) => {
        if (val === null) return '-';
        if (isPrivacyMode) return '₹ ••••••';
        return formatCurrency(val, 'INR');
    };

    const isProfit = entry.balance >= 0;

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-4 border-l-4 border-l-blue-500">
            <div className="flex justify-between items-start mb-3">
                <div className="flex flex-col max-w-[70%]">
                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">{entry.asset_name}</span>
                    <span className="text-[10px] text-gray-500 font-mono uppercase tracking-tighter">ISIN: {entry.isin}</span>
                </div>
                <div className="text-right">
                    <span className="text-[10px] bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded font-bold uppercase tracking-tighter italic">Schedule 112A</span>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-y-3 gap-x-4 py-3 border-t border-b border-gray-50 dark:border-gray-700">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Quantity</span>
                    <span className="text-xs font-semibold dark:text-gray-300">{Number(entry.quantity).toLocaleString()}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Sale Value</span>
                    <span className="text-xs font-semibold dark:text-gray-200">{formatVal(entry.full_value_consideration)}</span>
                </div>
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">Original Cost</span>
                    <span className="text-xs font-medium dark:text-gray-300">{formatVal(entry.cost_of_acquisition_orig)}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight">FMV 31-Jan-2018</span>
                    <span className="text-xs font-medium dark:text-gray-300">{formatVal(entry.fmv_31jan2018)}</span>
                </div>
            </div>

            <div className="mt-3 flex justify-between items-end">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Final Cost (COA)</span>
                    <span className="text-sm font-bold dark:text-gray-100">{formatVal(entry.cost_of_acquisition_final)}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Capital Gain</span>
                    <span className={`text-base font-extrabold ${isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {formatVal(entry.balance)}
                    </span>
                </div>
            </div>
        </div>
    );
};

export default Gain112ACard;

import React from 'react';
import { ScheduleFAEntry } from '../../hooks/useScheduleFA';
import { usePrivacy } from '../../context/PrivacyContext';

interface ScheduleFACardProps {
    entry: ScheduleFAEntry;
}

const ScheduleFACard: React.FC<ScheduleFACardProps> = ({ entry }) => {
    const { isPrivacyMode } = usePrivacy();

    const formatVal = (val: number, currency: string) => {
        if (isPrivacyMode) return `${currency} ••••••`;
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency,
            maximumFractionDigits: 0,
        }).format(val);
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-4">
            <div className="flex justify-between items-start mb-3">
                <div className="flex flex-col max-w-[70%]">
                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">{entry.entity_name}</span>
                    <div className="flex items-center gap-1">
                        <span className="text-[10px] text-gray-500 font-medium">{entry.country_name}</span>
                        {entry.country_code && entry.country_code.toUpperCase() !== entry.country_name.toUpperCase() && (
                            <span className="text-[9px] bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-1 rounded uppercase tracking-tighter">{entry.country_code}</span>
                        )}
                    </div>
                </div>
                <div className="text-right">
                    <span className="text-[10px] text-gray-400 font-mono uppercase">{entry.asset_ticker}</span>
                    <div className="text-[10px] font-medium text-gray-500 dark:text-gray-400">
                        {entry.date_acquired ? new Date(entry.date_acquired).toLocaleDateString('en-IN') : '-'}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-y-3 gap-x-4 py-3 border-t border-b border-gray-50 dark:border-gray-700">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Initial Value</span>
                    <span className="text-xs font-semibold dark:text-gray-200">{formatVal(entry.initial_value, entry.currency)}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Peak Value</span>
                    <span className="text-xs font-semibold text-green-600 dark:text-green-400">{formatVal(entry.peak_value, entry.currency)}</span>
                    {entry.peak_value_date && (
                        <div className="text-[8px] text-gray-400">
                            on {new Date(entry.peak_value_date).toLocaleDateString('en-IN')}
                        </div>
                    )}
                </div>
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Closing Balance</span>
                    <span className="text-xs font-semibold dark:text-gray-200">{formatVal(entry.closing_value, entry.currency)}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Gross Paid</span>
                    <span className="text-xs font-semibold dark:text-gray-200">{formatVal(entry.gross_amount_received, entry.currency)}</span>
                </div>
            </div>

            <div className="mt-3 pt-3 border-t border-gray-50 dark:border-gray-700 flex justify-between items-center">
                <div className="flex flex-col">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Nature</span>
                    <span className="text-xs dark:text-gray-300 italic">{entry.nature_of_entity}</span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Gross Proceeds</span>
                    <span className="text-sm font-extrabold text-orange-600 dark:text-orange-400">
                        {formatVal(entry.gross_proceeds_from_sale, entry.currency)}
                    </span>
                </div>
            </div>
        </div>
    );
};

export default ScheduleFACard;

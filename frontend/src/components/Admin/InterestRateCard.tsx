import React from 'react';
import { HistoricalInterestRate } from '../../types/interestRate';
import { formatDate } from '../../utils/formatting';
import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline';

interface InterestRateCardProps {
    rate: HistoricalInterestRate;
    onEdit: (rate: HistoricalInterestRate) => void;
    onDelete: (rate: HistoricalInterestRate) => void;
}

const InterestRateCard: React.FC<InterestRateCardProps> = ({ rate, onEdit, onDelete }) => {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-3 transition-all hover:shadow-md">
            <div className="flex justify-between items-start mb-2">
                <div className="flex flex-col max-w-[70%]">
                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">{rate.scheme_name}</span>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                            {formatDate(rate.start_date)} — {rate.end_date ? formatDate(rate.end_date) : 'Current'}
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-1">
                    <button onClick={() => onEdit(rate)} className="p-2 text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" aria-label={`Edit rate for ${rate.scheme_name}`}>
                        <PencilSquareIcon className="h-5 w-5" />
                    </button>
                    <button onClick={() => onDelete(rate)} className="p-2 text-gray-500 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" aria-label={`Delete rate for ${rate.scheme_name}`}>
                        <TrashIcon className="h-5 w-5" />
                    </button>
                </div>
            </div>

            <div className="mt-3 pt-3 border-t border-gray-50 dark:border-gray-700 flex justify-between items-center">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Interest Rate</span>
                    <span className="text-lg font-extrabold text-blue-600 dark:text-blue-400 font-mono">
                        {Number(rate.rate).toFixed(2)}%
                    </span>
                </div>
            </div>
        </div>
    );
};

export default InterestRateCard;

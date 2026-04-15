import React from 'react';
import { formatCurrency, formatPercentage } from '../../utils/formatting';
import { TopMover } from '../../types/dashboard';

interface TopMoversCardProps {
    asset: TopMover;
}

const TopMoversCard: React.FC<TopMoversCardProps> = ({ asset }) => {
    const getPnlColor = (value: number) => {
        if (value > 0) return 'text-green-600 dark:text-green-400';
        if (value < 0) return 'text-red-600 dark:text-red-400';
        return 'text-gray-800 dark:text-gray-200';
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-3 transition-all">
            <div className="flex justify-between items-center gap-3">
                <div className="flex flex-col min-w-0 flex-1">
                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">{asset.ticker_symbol}</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400 truncate">{asset.name}</span>
                </div>
                <div className="text-right flex-shrink-0 min-w-0">
                    <div className="text-sm font-mono font-bold text-gray-900 dark:text-gray-100 truncate">
                        {formatCurrency(asset.current_price, asset.currency)}
                    </div>
                    <div className={`text-[10px] xs:text-xs font-mono font-medium truncate ${getPnlColor(asset.daily_change)}`}>
                        {asset.daily_change > 0 && '+'}
                        {formatCurrency(asset.daily_change, 'INR')}
                        <span className="ml-1">({formatPercentage(asset.daily_change_percentage)})</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TopMoversCard;

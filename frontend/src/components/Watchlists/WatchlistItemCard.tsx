import React from 'react';
import { WatchlistItem } from '../../types/watchlist';
import { useRemoveWatchlistItem } from '../../hooks/useWatchlists';
import { TrashIcon } from '@heroicons/react/24/solid';
import { formatCurrency } from '../../utils/formatting';

interface WatchlistItemCardProps {
    item: WatchlistItem;
    watchlistId: string;
}

const WatchlistItemCard: React.FC<WatchlistItemCardProps> = ({ item, watchlistId }) => {
    const removeWatchlistItem = useRemoveWatchlistItem();

    const handleRemove = () => {
        removeWatchlistItem.mutate({ watchlistId, itemId: item.id });
    };

    const getPnlColor = (pnl: number | undefined) => {
        if (!pnl) return 'text-gray-900 dark:text-gray-200';
        if (pnl > 0) return 'text-green-600 dark:text-green-400';
        if (pnl < 0) return 'text-red-600 dark:text-red-400';
        return 'text-gray-900 dark:text-gray-200';
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-3 transition-all">
            <div className="flex justify-between items-start">
                <div className="flex flex-col max-w-[70%]">
                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">{item.asset.ticker_symbol}</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400 truncate">{item.asset.name}</span>
                </div>
                <button
                    onClick={handleRemove}
                    className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    aria-label={`Remove ${item.asset.ticker_symbol}`}
                >
                    <TrashIcon className="h-5 w-5" />
                </button>
            </div>

            <div className="mt-3 pt-3 border-t border-gray-50 dark:border-gray-700 flex justify-between items-center">
                <div>
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Current Price</span>
                    <span className="text-sm font-mono font-bold text-gray-900 dark:text-gray-100">
                        {item.asset.current_price ? formatCurrency(item.asset.current_price, item.asset.currency) : <span className="text-gray-400">N/A</span>}
                    </span>
                </div>
                <div className="text-right">
                    <span className="block text-[10px] text-gray-500 uppercase tracking-tight font-bold">Day's Change</span>
                    <span className={`text-sm font-mono font-bold ${getPnlColor(item.asset.day_change)}`}>
                        {item.asset.day_change !== undefined ? formatCurrency(item.asset.day_change, item.asset.currency) : <span className="text-gray-400">N/A</span>}
                    </span>
                </div>
            </div>
        </div>
    );
};

export default WatchlistItemCard;

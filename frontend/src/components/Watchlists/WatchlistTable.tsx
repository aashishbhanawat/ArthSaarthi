import React from 'react';
import { Watchlist } from '../../types/watchlist';
import { useRemoveWatchlistItem } from '../../hooks/useWatchlists';
import { TrashIcon } from '@heroicons/react/24/solid';
import { formatCurrency } from '../../utils/formatting';
import WatchlistItemCard from './WatchlistItemCard';

interface WatchlistTableProps {
  watchlist: Watchlist | undefined;
  isLoading: boolean;
  error: Error | null;
}

const PnlCell: React.FC<{ value: number | undefined; currency?: string | null }> = ({ value, currency }) => {
    if (value === undefined || value === null) {
        return <td className="p-2 text-right font-mono text-gray-500">N/A</td>;
    }

    const getPnlColor = (pnl: number) => {
        if (pnl > 0) return 'text-green-600';
        if (pnl < 0) return 'text-red-600';
        return 'text-gray-900';
    };

    return (
        <td className={`p-2 text-right font-mono ${getPnlColor(value)}`}>
            {formatCurrency(value, currency)}
        </td>
    );
};

const WatchlistTable: React.FC<WatchlistTableProps> = ({ watchlist, isLoading, error }) => {
  const removeWatchlistItem = useRemoveWatchlistItem();

  const handleRemove = (itemId: string) => {
    if (watchlist) {
      removeWatchlistItem.mutate({ watchlistId: watchlist.id, itemId });
    }
  };

  if (isLoading) {
    return <div className="text-center p-8 text-gray-500">Loading assets...</div>;
  }

  if (error) {
    return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;
  }

  if (!watchlist || watchlist.items.length === 0) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-500">This watchlist is empty.</p>
        <p className="text-sm text-gray-400 mt-2">Add assets to start tracking.</p>
      </div>
    );
  }

  return (
    <div className="mt-4">
      {/* Desktop Table View */}
      <div className="hidden lg:block overflow-x-auto">
        <table className="table-auto w-full">
          <thead>
            <tr className="text-left text-gray-600 text-sm border-b dark:border-gray-700">
              <th className="p-2">Asset</th>
              <th className="p-2 text-right">Current Price</th>
              <th className="p-2 text-right">Day's Change</th>
              <th className="p-2 text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {watchlist.items.map((item) => (
              <tr key={item.id} className="border-b dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors">
                <td className="p-2">
                  <div className="font-bold text-gray-900 dark:text-gray-100">{item.asset.ticker_symbol}</div>
                  <div className="text-sm text-gray-500 truncate max-w-[200px]">{item.asset.name}</div>
                </td>
                <td className="p-2 text-right font-mono text-gray-900 dark:text-gray-200">
                  {item.asset.current_price ? formatCurrency(item.asset.current_price, item.asset.currency) : <span className="text-gray-500">N/A</span>}
                </td>
                <PnlCell value={item.asset.day_change} currency={item.asset.currency} />
                <td className="p-2 text-center">
                  <button
                    onClick={() => handleRemove(item.id)}
                    className="btn btn-ghost btn-xs text-gray-400 hover:text-red-500"
                    aria-label={`Remove ${item.asset.ticker_symbol}`}
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="lg:hidden">
        {watchlist.items.map((item) => (
          <WatchlistItemCard key={item.id} item={item} watchlistId={watchlist.id} />
        ))}
      </div>
    </div>
  );
};

export default WatchlistTable;


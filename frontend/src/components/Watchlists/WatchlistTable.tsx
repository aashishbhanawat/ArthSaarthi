import React from 'react';
import { Watchlist } from '../../types/watchlist';
import { useRemoveWatchlistItem } from '../../hooks/useWatchlists';
import { TrashIcon } from '@heroicons/react/24/solid';
import { formatCurrency } from '../../utils/formatting';

interface WatchlistTableProps {
  watchlist: Watchlist | undefined;
  isLoading: boolean;
  error: Error | null;
}

const PnlCell: React.FC<{ value: number | undefined }> = ({ value }) => {
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
            {formatCurrency(value)}
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
    return <div>Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error: {error.message}</div>;
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
    <div className="overflow-x-auto">
      <table className="table-auto w-full">
        <thead>
          <tr className="text-left text-gray-600 text-sm">
            <th className="p-2">Asset</th>
            <th className="p-2 text-right">Current Price</th>
            <th className="p-2 text-right">Day's Change</th>
            <th className="p-2 text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          {watchlist.items.map((item) => (
            <tr key={item.id} className="border-t">
              <td className="p-2">
                <div className="font-bold">{item.asset.ticker_symbol}</div>
                <div className="text-sm text-gray-500 truncate">{item.asset.name}</div>
              </td>
              <td className="p-2 text-right font-mono">
                {item.asset.current_price ? formatCurrency(item.asset.current_price) : <span className="text-gray-500">N/A</span>}
              </td>
              <PnlCell value={item.asset.day_change} />
              <td className="p-2 text-center">
                <button
                  onClick={() => handleRemove(item.id)}
                  className="btn btn-ghost btn-xs"
                  aria-label={`Remove ${item.asset.ticker_symbol}`}
                >
                  <TrashIcon className="h-4 w-4 text-red-500" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default WatchlistTable;

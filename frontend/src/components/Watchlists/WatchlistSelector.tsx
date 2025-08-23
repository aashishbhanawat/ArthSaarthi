import React from 'react';
import { Select } from 'flowbite-react';
import { Watchlist } from '../../types/watchlist';

interface WatchlistSelectorProps {
  watchlists: Watchlist[];
  selectedWatchlistId: string | null;
  onSelectWatchlist: (id: string) => void;
  className?: string;
}

const WatchlistSelector: React.FC<WatchlistSelectorProps> = ({
  watchlists,
  selectedWatchlistId,
  onSelectWatchlist,
  className
}) => {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <label htmlFor="watchlist-selector" className="text-sm font-medium text-gray-700">
        Watchlist:
      </label>
      <Select
        id="watchlist-selector"
        value={selectedWatchlistId || ''}
        onChange={(e) => onSelectWatchlist(e.target.value)}
        className="w-48"
      >
        {watchlists.map((watchlist) => (
          <option key={watchlist.id} value={watchlist.id}>
            {watchlist.name}
          </option>
        ))}
      </Select>
    </div>
  );
};

export default WatchlistSelector;

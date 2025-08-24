import React, { useState } from 'react';
import WatchlistSelector from '../components/Watchlists/WatchlistSelector';

const WatchlistsPage: React.FC = () => {
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<string | null>(null);

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <WatchlistSelector
            selectedWatchlistId={selectedWatchlistId}
            onSelectWatchlist={setSelectedWatchlistId}
          />
        </div>
        <div className="lg:col-span-3">
          <div className="bg-base-100 p-4 rounded-lg shadow">
            <h1 className="text-2xl font-bold mb-4">
              Watchlist Items
            </h1>
            {selectedWatchlistId ? (
              <p>Displaying items for watchlist ID: {selectedWatchlistId}</p>
            ) : (
              <p>Please select a watchlist to view its items.</p>
            )}
            {/* WatchlistTable will go here in Phase 3 */}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WatchlistsPage;

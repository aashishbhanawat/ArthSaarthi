import React, { useState } from 'react';
import WatchlistSelector from '../components/Watchlists/WatchlistSelector';
import WatchlistTable from '../components/Watchlists/WatchlistTable';
import AddAssetToWatchlistModal from '../components/modals/AddAssetToWatchlistModal';
import { useWatchlist, useAddWatchlistItem } from '../hooks/useWatchlists';
import { PlusIcon } from '@heroicons/react/24/solid';

const WatchlistsPage: React.FC = () => {
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  const { data: selectedWatchlist, isLoading, error } = useWatchlist(selectedWatchlistId);
  const addWatchlistItem = useAddWatchlistItem();

  const handleAddAsset = (assetId: string) => {
    if (selectedWatchlistId) {
      addWatchlistItem.mutate({ watchlistId: selectedWatchlistId, item: { asset_id: assetId } });
    }
  };

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
            <div className="flex justify-between items-center mb-4">
              <h1 className="text-2xl font-bold">
                {selectedWatchlist ? selectedWatchlist.name : 'Select a Watchlist'}
              </h1>
              {selectedWatchlistId && (
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => setIsAddModalOpen(true)}
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Add Asset
                </button>
              )}
            </div>
            <WatchlistTable
              watchlist={selectedWatchlist}
              isLoading={isLoading}
              error={error}
            />
          </div>
        </div>
      </div>
      <AddAssetToWatchlistModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAddAsset={handleAddAsset}
      />
    </div>
  );
};

export default WatchlistsPage;

import React, { useState, useMemo } from 'react';
import { Button, Card } from 'flowbite-react';
import { useWatchlists } from '../hooks/useWatchlists';
import WatchlistSelector from '../components/Watchlists/WatchlistSelector';
import WatchlistTable from '../components/Watchlists/WatchlistTable';
import WatchlistFormModal from '../components/modals/WatchlistFormModal';
import AddAssetToWatchlistModal from '../components/modals/AddAssetToWatchlistModal';
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/solid';

const WatchlistsPage: React.FC = () => {
  const {
    watchlists,
    isLoading,
    error,
    createWatchlist,
    updateWatchlist,
    deleteWatchlist,
    addWatchlistItem,
    deleteWatchlistItem,
  } = useWatchlists();

  const [selectedWatchlistId, setSelectedWatchlistId] = useState<string | null>(null);
  const [isNewWatchlistModalOpen, setIsNewWatchlistModalOpen] = useState(false);
  const [isEditWatchlistModalOpen, setIsEditWatchlistModalOpen] = useState(false);
  const [isAddAssetModalOpen, setIsAddAssetModalOpen] = useState(false);

  const selectedWatchlist = useMemo(() => {
    if (!selectedWatchlistId) return watchlists?.[0];
    return watchlists?.find((w) => w.id === selectedWatchlistId);
  }, [watchlists, selectedWatchlistId]);

  React.useEffect(() => {
    if (!selectedWatchlistId && watchlists && watchlists.length > 0) {
      setSelectedWatchlistId(watchlists[0].id);
    }
  }, [watchlists, selectedWatchlistId]);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading watchlists</div>;

  const handleCreateWatchlist = (name: string) => {
    createWatchlist({ name });
    setIsNewWatchlistModalOpen(false);
  };

  const handleUpdateWatchlist = (name: string) => {
    if (selectedWatchlist) {
      updateWatchlist({ id: selectedWatchlist.id, updatedWatchlist: { name } });
    }
    setIsEditWatchlistModalOpen(false);
  };

  const handleDeleteWatchlist = () => {
    if (selectedWatchlist && window.confirm(`Are you sure you want to delete the "${selectedWatchlist.name}" watchlist?`)) {
      deleteWatchlist(selectedWatchlist.id);
      setSelectedWatchlistId(null);
    }
  };

  const handleAddAsset = (assetId: string) => {
    if (selectedWatchlist) {
      addWatchlistItem({ watchlistId: selectedWatchlist.id, item: { asset_id: assetId } });
    }
    // Note: We could choose to close the modal upon adding an asset, or keep it open for multiple additions.
    // For now, we'll keep it open.
  };

  const handleRemoveItem = (itemId: string) => {
    if (selectedWatchlist) {
      deleteWatchlistItem({ watchlistId: selectedWatchlist.id, itemId });
    }
  };

  return (
    <div className="container mx-auto p-4">
      <Card>
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4">
          <h1 className="text-2xl font-bold mb-4 sm:mb-0">Watchlists</h1>
          <div className="flex items-center space-x-2">
            {watchlists && watchlists.length > 0 && (
              <WatchlistSelector
                watchlists={watchlists}
                selectedWatchlistId={selectedWatchlist?.id ?? null}
                onSelectWatchlist={setSelectedWatchlistId}
              />
            )}
            <Button onClick={() => setIsNewWatchlistModalOpen(true)} color="blue">
              <PlusIcon className="h-5 w-5 mr-2" /> New
            </Button>
            {selectedWatchlist && (
              <>
                <Button onClick={() => setIsEditWatchlistModalOpen(true)} color="gray">
                  <PencilIcon className="h-5 w-5" />
                </Button>
                <Button onClick={handleDeleteWatchlist} color="failure">
                  <TrashIcon className="h-5 w-5" />
                </Button>
              </>
            )}
          </div>
        </div>

        {selectedWatchlist && (
          <div className="flex justify-end mb-4">
            <Button onClick={() => setIsAddAssetModalOpen(true)}>
              <PlusIcon className="h-5 w-5 mr-2" /> Add Asset
            </Button>
          </div>
        )}

        <WatchlistTable watchlist={selectedWatchlist} onRemoveItem={handleRemoveItem} />
      </Card>

      <WatchlistFormModal
        isOpen={isNewWatchlistModalOpen}
        onClose={() => setIsNewWatchlistModalOpen(false)}
        onSubmit={handleCreateWatchlist}
      />

      {selectedWatchlist && (
        <WatchlistFormModal
          isOpen={isEditWatchlistModalOpen}
          onClose={() => setIsEditWatchlistModalOpen(false)}
          onSubmit={handleUpdateWatchlist}
          initialWatchlist={selectedWatchlist}
        />
      )}

      <AddAssetToWatchlistModal
        isOpen={isAddAssetModalOpen}
        onClose={() => setIsAddAssetModalOpen(false)}
        onAddAsset={handleAddAsset}
      />
    </div>
  );
};

export default WatchlistsPage;

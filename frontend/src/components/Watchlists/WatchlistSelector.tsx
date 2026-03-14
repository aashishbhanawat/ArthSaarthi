import React, { useState } from 'react';
import {
  useWatchlists,
  useCreateWatchlist,
  useUpdateWatchlist,
  useDeleteWatchlist,
} from '../../hooks/useWatchlists';
import WatchlistFormModal from '../modals/WatchlistFormModal';
import { DeleteConfirmationModal } from '../common/DeleteConfirmationModal';
import { Watchlist } from '../../types/watchlist';
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/solid';

interface WatchlistSelectorProps {
  selectedWatchlistId: string | null;
  onSelectWatchlist: (id: string | null) => void;
}

const WatchlistSelector: React.FC<WatchlistSelectorProps> = ({
  selectedWatchlistId,
  onSelectWatchlist,
}) => {
  const { data: watchlists, isLoading, error } = useWatchlists();
  const createWatchlist = useCreateWatchlist();
  const updateWatchlist = useUpdateWatchlist();
  const deleteWatchlist = useDeleteWatchlist();

  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [editingWatchlist, setEditingWatchlist] = useState<Watchlist | null>(null);
  const [watchlistToDelete, setWatchlistToDelete] = useState<Watchlist | null>(null);

  const handleCreate = () => {
    setEditingWatchlist(null);
    setIsFormModalOpen(true);
  };

  const handleEdit = (watchlist: Watchlist) => {
    setEditingWatchlist(watchlist);
    setIsFormModalOpen(true);
  };

  const handleDelete = (watchlist: Watchlist) => {
    setWatchlistToDelete(watchlist);
  };

  const confirmDelete = () => {
    if (watchlistToDelete) {
      deleteWatchlist.mutate(watchlistToDelete.id, {
        onSuccess: () => {
          if (selectedWatchlistId === watchlistToDelete.id) {
            onSelectWatchlist(null);
          }
          setWatchlistToDelete(null);
        },
      });
    }
  };

  const handleFormSubmit = (name: string) => {
    if (editingWatchlist) {
      updateWatchlist.mutate({ id: editingWatchlist.id, name });
    } else {
      createWatchlist.mutate(name);
    }
  };

  if (isLoading) return <div>Loading watchlists...</div>;
  if (error) return <div>Error loading watchlists: {error.message}</div>;

  return (
    <div className="p-4 bg-base-200 rounded-lg">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-bold">My Watchlists</h2>
        <button className="btn btn-sm btn-primary" onClick={handleCreate} aria-label="Add new watchlist">
          <PlusIcon className="h-4 w-4" />
        </button>
      </div>
      <ul className="menu bg-base-100 rounded-box">
        {watchlists?.map((watchlist) => (
          <li
            key={watchlist.id}
            className={selectedWatchlistId === watchlist.id ? 'bordered' : ''}
          >
            <a
              onClick={() => onSelectWatchlist(watchlist.id)}
              className="flex justify-between items-center"
            >
              <span>{watchlist.name}</span>
              <div className="flex items-center gap-2">
                <button
                  className="btn btn-ghost btn-xs"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleEdit(watchlist);
                  }}
                  aria-label={`Edit ${watchlist.name}`}
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button
                  className="btn btn-ghost btn-xs"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(watchlist);
                  }}
                  aria-label={`Delete ${watchlist.name}`}
                >
                  <TrashIcon className="h-4 w-4 text-red-500" />
                </button>
              </div>
            </a>
          </li>
        ))}
      </ul>
      <WatchlistFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        onSubmit={handleFormSubmit}
        watchlist={editingWatchlist}
        isPending={createWatchlist.isPending || updateWatchlist.isPending}
      />
      <DeleteConfirmationModal
        isOpen={!!watchlistToDelete}
        onClose={() => setWatchlistToDelete(null)}
        onConfirm={confirmDelete}
        title="Delete Watchlist"
        message={
          <>
            Are you sure you want to delete the watchlist "<strong>{watchlistToDelete?.name}</strong>"?
          </>
        }
        isDeleting={deleteWatchlist.isPending}
      />
    </div>
  );
};

export default WatchlistSelector;

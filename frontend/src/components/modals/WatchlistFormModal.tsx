import React, { useState, useEffect } from 'react';
import { Watchlist } from '../../types/watchlist';
import { ArrowPathIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface WatchlistFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (name: string) => void;
  watchlist?: Watchlist | null; // Provide for editing
  isPending?: boolean;
}

const WatchlistFormModal: React.FC<WatchlistFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  watchlist,
  isPending = false,
}) => {
  const [name, setName] = useState('');
  const isEditMode = !!watchlist;

  useEffect(() => {
    if (isOpen) {
      setName(isEditMode ? watchlist.name : '');
    }
  }, [isOpen, isEditMode, watchlist]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      onSubmit(name);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="watchlist-modal-title"
    >
      <div className="modal-content max-w-md">
        <div className="modal-header flex justify-between items-center">
          <h2 id="watchlist-modal-title" className="text-2xl font-bold">
            {isEditMode ? 'Rename Watchlist' : 'Create New Watchlist'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            disabled={isPending}
            aria-label="Close"
          >
            <XMarkIcon className="h-6 w-6" aria-hidden="true" />
          </button>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="watchlistName">
                Watchlist Name
              </label>
              <input
                id="watchlistName"
                type="text"
                placeholder="E.g., Tech Stocks"
                className="form-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="flex items-center justify-end pt-4">
              <button type="button" onClick={onClose} className="btn btn-secondary mr-2" disabled={isPending}>
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary flex items-center gap-2"
                disabled={isPending || !name.trim()}
              >
                {isPending && <ArrowPathIcon className="h-4 w-4 animate-spin" aria-hidden="true" />}
                {isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default WatchlistFormModal;

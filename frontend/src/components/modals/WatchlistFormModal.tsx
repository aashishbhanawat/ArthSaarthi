import React, { useState, useEffect } from 'react';
import { Watchlist } from '../../types/watchlist';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

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
      className="modal modal-open"
      role="dialog"
      aria-modal="true"
      aria-labelledby="watchlist-modal-title"
    >
      <div className="modal-box">
        <h3 id="watchlist-modal-title" className="font-bold text-lg">
          {isEditMode ? 'Rename Watchlist' : 'Create New Watchlist'}
        </h3>
        <form onSubmit={handleSubmit}>
          <div className="form-control w-full py-4">
            <label className="label" htmlFor="watchlistName">
              <span className="label-text">Watchlist Name</span>
            </label>
            <input
              id="watchlistName"
              type="text"
              placeholder="E.g., Tech Stocks"
              className="input input-bordered w-full"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="modal-action">
            <button type="button" onClick={onClose} className="btn btn-ghost" disabled={isPending}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary flex items-center gap-2"
              disabled={isPending || !name.trim()}
            >
              {isPending && <ArrowPathIcon className="h-4 w-4 animate-spin" />}
              {isPending ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default WatchlistFormModal;

import React, { useState, useEffect } from 'react';
import { Watchlist } from '../../types/watchlist';

interface WatchlistFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (name: string) => void;
  watchlist?: Watchlist | null; // Provide for editing
}

const WatchlistFormModal: React.FC<WatchlistFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  watchlist,
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
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box">
        <h3 className="font-bold text-lg">
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
            <button type="button" onClick={onClose} className="btn btn-ghost">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={!name.trim()}>
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default WatchlistFormModal;

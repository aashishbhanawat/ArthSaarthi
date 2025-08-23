import React, { useState, useEffect } from 'react';
import { Modal, Button, TextInput } from 'flowbite-react';
import { Watchlist } from '../../types/watchlist';

interface WatchlistFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (name: string) => void;
  initialWatchlist?: Watchlist | null;
}

const WatchlistFormModal: React.FC<WatchlistFormModalProps> = ({ isOpen, onClose, onSubmit, initialWatchlist }) => {
  const [name, setName] = useState('');

  useEffect(() => {
    if (initialWatchlist) {
      setName(initialWatchlist.name);
    } else {
      setName('');
    }
  }, [initialWatchlist, isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(name);
  };

  return (
    <Modal show={isOpen} onClose={onClose}>
      <Modal.Header>{initialWatchlist ? 'Edit Watchlist' : 'Create New Watchlist'}</Modal.Header>
      <Modal.Body>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Watchlist Name
              </label>
              <TextInput
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="mt-1"
              />
            </div>
          </div>
        </form>
      </Modal.Body>
      <Modal.Footer>
        <Button onClick={handleSubmit} color="blue">
          {initialWatchlist ? 'Save' : 'Create'}
        </Button>
        <Button color="gray" onClick={onClose}>
          Cancel
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default WatchlistFormModal;

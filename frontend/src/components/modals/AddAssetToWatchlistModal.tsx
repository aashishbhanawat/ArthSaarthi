import React, { useState, useEffect, useMemo } from 'react';
import { useAssetSearch } from '../../hooks/useAssets';
import { Asset } from '../../types/asset';
import { XMarkIcon } from '@heroicons/react/24/solid';
import { useDebounce } from '../../hooks/useDebounce';

interface AddAssetToWatchlistModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddAsset: (assetId: string) => void;
}

const AddAssetToWatchlistModal: React.FC<AddAssetToWatchlistModalProps> = ({
  isOpen,
  onClose,
  onAddAsset,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  const { data: searchResults, isLoading } = useAssetSearch(debouncedSearchTerm);

  useEffect(() => {
    if (!isOpen) {
      setSearchTerm('');
      setSelectedAsset(null);
    }
  }, [isOpen]);

  const handleAdd = () => {
    if (selectedAsset) {
      onAddAsset(selectedAsset.id);
      onClose();
    }
  };

  const filteredResults = useMemo(() => {
    if (!searchResults) return [];
    if (selectedAsset) {
      return searchResults.filter((asset) => asset.id !== selectedAsset.id);
    }
    return searchResults;
  }, [searchResults, selectedAsset]);

  if (!isOpen) return null;

  return (
    <div className="modal modal-open" role="dialog" aria-labelledby="add-asset-modal-title">
      <div className="modal-box">
        <button
          onClick={onClose}
          className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
          aria-label="Close"
        >
          ✕
        </button>
        <h3 id="add-asset-modal-title" className="font-bold text-lg">Add Asset to Watchlist</h3>

        <div className="form-control w-full mt-4">
          <label className="label" htmlFor="asset-search-input">
            <span className="label-text">Search for an asset</span>
          </label>
          <div className="dropdown w-full">
            <input
              id="asset-search-input"
              type="text"
              placeholder="Search for assets..."
              className="input input-bordered w-full"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {debouncedSearchTerm && (
              <ul className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-full mt-1">
                {isLoading && <li><a>Loading...</a></li>}
                {filteredResults.map((asset) => (
                  <li key={asset.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedAsset(asset);
                        setSearchTerm(asset.name);
                      }}
                    >
                      {asset.name} ({asset.ticker_symbol})
                    </button>
                  </li>
                ))}
                {!isLoading && filteredResults.length === 0 && (
                  <li><a>No results found</a></li>
                )}
              </ul>
            )}
          </div>
        </div>

        {selectedAsset && (
          <div className="alert alert-info mt-4">
            <div className="flex-1">
              <span className="label-text">Selected: {selectedAsset.name}</span>
            </div>
            <button
              onClick={() => setSelectedAsset(null)}
              className="btn btn-ghost btn-sm"
              aria-label="Clear selection"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
        )}

        <div className="modal-action">
          <button type="button" onClick={onClose} className="btn btn-ghost">
            Cancel
          </button>
          <button
            onClick={handleAdd}
            className="btn btn-primary"
            disabled={!selectedAsset}
          >
            Add Asset to Watchlist
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddAssetToWatchlistModal;

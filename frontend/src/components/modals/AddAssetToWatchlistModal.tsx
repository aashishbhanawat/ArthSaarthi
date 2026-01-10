import React, { useState, useEffect, useMemo } from 'react';
import { useAssetSearch } from '../../hooks/useAssets';
import { AssetSearchResult } from '../../services/portfolioApi';
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
  const [selectedAsset, setSelectedAsset] = useState<AssetSearchResult | null>(null);
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  const { data: searchResults, isLoading } = useAssetSearch(debouncedSearchTerm);

  useEffect(() => {
    if (!isOpen) {
      setSearchTerm('');
      setSelectedAsset(null);
    }
  }, [isOpen]);

  const handleAdd = () => {
    if (selectedAsset && selectedAsset.id) {
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
                {!isLoading &&
                  filteredResults.length === 0 &&
                  !selectedAsset && <li><a>No results found</a></li>}
              </ul>
            )}
          </div>
        </div>

        <div className="modal-action mt-6 flex justify-between items-center w-full">
          <div className="flex-1 min-w-0">
            {selectedAsset && (
              <div className="flex items-center gap-2 text-sm">
                <span className="font-semibold">Selected:</span>
                <span className="truncate" title={selectedAsset.name}>{selectedAsset.name}</span>
                <button
                  onClick={() => setSelectedAsset(null)}
                  className="btn btn-ghost btn-xs btn-circle"
                  aria-label="Clear selection"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>
          <div className="flex-shrink-0 flex items-center gap-2">
            <button type="button" onClick={onClose} className="btn btn-ghost">Cancel</button>
            <button onClick={handleAdd} className="btn btn-primary" disabled={!selectedAsset}>Add Asset to Watchlist</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddAssetToWatchlistModal;

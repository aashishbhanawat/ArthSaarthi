import React, { useState, useEffect, useMemo } from 'react';
import { useAssetSearch } from '../../hooks/useAssets';
import { AssetSearchResult, lookupAsset } from '../../services/portfolioApi';
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
  const [isAdding, setIsAdding] = useState(false);
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  const { data: searchResults, isLoading } = useAssetSearch(debouncedSearchTerm);

  useEffect(() => {
    if (!isOpen) {
      setSearchTerm('');
      setSelectedAsset(null);
      setIsAdding(false);
    }
  }, [isOpen]);

  const handleAdd = async () => {
    if (!selectedAsset) return;

    if (selectedAsset.id) {
      onAddAsset(selectedAsset.id);
      onClose();
      return;
    }

    // Asset has no ID (external/foreign), create it first
    setIsAdding(true);
    try {
      // Use lookupAsset to create the asset in the backend
      // Passing forceExternal=true ensures we try to create it if not found locally (which is known since no ID)
      const assets = await lookupAsset(selectedAsset.ticker_symbol, selectedAsset.asset_type, true);
      if (assets && assets.length > 0) {
        onAddAsset(assets[0].id);
        onClose();
      } else {
        console.error('Failed to create asset: No asset returned from lookup');
      }
    } catch (error) {
      console.error('Error creating asset:', error);
    } finally {
      setIsAdding(false);
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
    <div className="modal-overlay" role="dialog" aria-labelledby="add-asset-modal-title" onClick={onClose}>
      <div className="modal-content max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 id="add-asset-modal-title" className="text-2xl font-bold">Add Asset to Watchlist</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            aria-label="Close"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="form-group w-full mt-4">
          <label className="form-label" htmlFor="asset-search-input">
            Search for an asset
          </label>
          <div className="relative w-full">
            <input
              id="asset-search-input"
              type="text"
              placeholder="Search for assets..."
              className="form-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {debouncedSearchTerm && (
              <ul className="absolute z-10 w-full bg-white dark:bg-gray-800 border dark:border-gray-600 rounded-md mt-1 max-h-60 overflow-y-auto shadow-lg divide-y dark:divide-gray-700">
                {isLoading && <li className="p-3 text-sm text-gray-500">Loading...</li>}
                {filteredResults.map((asset) => (
                  <li key={asset.id || asset.ticker_symbol}>
                    <button
                      type="button"
                      className="w-full text-left p-3 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      onClick={() => {
                        setSelectedAsset(asset);
                        setSearchTerm(asset.name);
                      }}
                    >
                      <div className="font-medium">{asset.name}</div>
                      <div className="text-xs text-gray-500">({asset.ticker_symbol})</div>
                    </button>
                  </li>
                ))}
                {!isLoading &&
                  filteredResults.length === 0 &&
                  !selectedAsset && <li className="p-3 text-sm text-gray-500">No results found</li>}
              </ul>
            )}
          </div>
        </div>

        <div className="mt-8">
          {selectedAsset && (
            <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg mb-6 border border-blue-100 dark:border-blue-800">
              <div className="flex-1 min-w-0">
                <span className="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase block">Selected</span>
                <span className="text-sm font-medium truncate block" title={selectedAsset.name}>{selectedAsset.name}</span>
              </div>
              <button
                onClick={() => setSelectedAsset(null)}
                className="text-blue-500 hover:text-blue-700 p-1"
                aria-label="Clear selection"
                disabled={isAdding}
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn btn-secondary" disabled={isAdding}>Cancel</button>
          <button
            onClick={handleAdd}
            className="btn btn-primary"
            disabled={!selectedAsset || isAdding}
          >
            {isAdding ? 'Adding...' : 'Add to Watchlist'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddAssetToWatchlistModal;

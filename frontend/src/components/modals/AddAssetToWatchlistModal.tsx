import React, { useState, useEffect } from 'react';
import React, { useState, useEffect } from 'react';
import { useAssetSearch, useCreateAsset } from '../../hooks/useAssets';
import { Asset } from '../../types/asset';

interface AddAssetToWatchlistModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddAsset: (assetId: string) => void;
  existingAssetIds: string[];
}

const AddAssetToWatchlistModal: React.FC<AddAssetToWatchlistModalProps> = ({
  isOpen,
  onClose,
  onAddAsset,
  existingAssetIds,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: assets, isLoading } = useAssetSearch(searchTerm);
  const addAssetToWatchlist = useAddAssetToWatchlist();

  const [filteredAssets, setFilteredAssets] = useState<Asset[]>([]);

  useEffect(() => {
    if (assets) {
      const newFilteredAssets = assets.filter(
        (asset) =>
          !existingAssetIds.includes(asset.id) &&
          (asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            asset.symbol.toLowerCase().includes(searchTerm.toLowerCase()))
      );
      setFilteredAssets(newFilteredAssets);
    }
  }, [assets, searchTerm, existingAssetIds]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
      <div className="relative mx-auto p-5 border w-full max-w-md m-4 bg-white rounded-lg shadow-lg">
        <div className="flex justify-between items-center pb-3">
          <p className="text-2xl font-bold">Add Asset to Watchlist</p>
          <div className="modal-close cursor-pointer z-50" onClick={onClose}>
            <svg className="fill-current text-black" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">
              <path d="M14.53 4.53l-1.06-1.06L9 7.94 4.53 3.47 3.47 4.53 7.94 9l-4.47 4.47 1.06 1.06L9 10.06l4.47 4.47 1.06-1.06L10.06 9z"></path>
            </svg>
          </div>
        </div>
        <div className="my-4">
          <input
            type="text"
            placeholder="Search for an asset..."
            className="w-full p-2 border border-gray-300 rounded-md"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <div className="mt-4 max-h-60 overflow-y-auto">
            {isLoading && <p>Loading assets...</p>}
            {filteredAssets.length > 0 ? (
              filteredAssets.map((asset) => (
                <div
                  key={asset.id}
                  className="flex items-center justify-between p-2 hover:bg-gray-100 cursor-pointer"
                  onClick={() => handleAddAsset(asset.id)}
                >
                  <div>
                    <p className="font-bold">{asset.symbol}</p>
                    <p className="text-sm text-gray-500">{asset.name}</p>
                  </div>
                  <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    Add
                  </button>
                </div>
              ))
            ) : (
              <p className="text-gray-500">No assets found.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddAssetToWatchlistModal;

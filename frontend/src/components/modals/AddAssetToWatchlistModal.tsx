import React, { useState, useEffect } from 'react';
import { useAssetSearch } from '../../hooks/usePortfolios';
import { Asset } from '../../types/asset';

// A simple debounce hook
const useDebounce = (value: string, delay: number) => {
    const [debouncedValue, setDebouncedValue] = useState(value);
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);
        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);
    return debouncedValue;
};

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
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const debouncedSearchTerm = useDebounce(searchTerm, 300);
    const { data: searchResults, isLoading } = useAssetSearch(debouncedSearchTerm);

    const handleAdd = () => {
        if (selectedAsset) {
            onAddAsset(selectedAsset.id);
            onClose();
        }
    };

    // Reset state when modal opens/closes
    useEffect(() => {
        if (!isOpen) {
            setSearchTerm('');
            setSelectedAsset(null);
        }
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div className="modal modal-open">
            <div className="modal-box">
                <h3 className="font-bold text-lg">Add Asset to Watchlist</h3>
                <div className="form-control w-full py-4">
                    <label className="label" htmlFor="assetSearch">
                        <span className="label-text">Search for Asset</span>
                    </label>
                    <input
                        id="assetSearch"
                        type="text"
                        placeholder="Type to search by name or ticker..."
                        className="input input-bordered w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                {isLoading && <span className="loading loading-spinner loading-sm"></span>}

                {searchResults && (
                    <ul className="menu bg-base-100 w-full rounded-box mt-2 border max-h-60 overflow-y-auto">
                        {searchResults.map((asset) => (
                            <li key={asset.id} onClick={() => setSelectedAsset(asset)}>
                                <a className={selectedAsset?.id === asset.id ? 'active' : ''}>
                                    {asset.name} ({asset.ticker_symbol})
                                </a>
                            </li>
                        ))}
                    </ul>
                )}

                <div className="modal-action">
                    <button onClick={onClose} className="btn btn-ghost">Cancel</button>
                    <button onClick={handleAdd} className="btn btn-primary" disabled={!selectedAsset}>
                        Add Asset
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AddAssetToWatchlistModal;

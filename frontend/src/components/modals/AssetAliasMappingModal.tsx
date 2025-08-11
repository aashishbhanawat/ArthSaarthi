import React, { useState, useEffect } from 'react';
import { useAssetSearch } from '../../hooks/usePortfolio';
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

interface AssetAliasMappingModalProps {
    isOpen: boolean;
    onClose: () => void;
    unrecognizedTicker: string;
    portfolioId: string; // Keep portfolioId in case we need it later
    onAliasCreated: (alias: { alias_symbol: string; asset_id: string, source: string }) => void;
}

const AssetAliasMappingModal: React.FC<AssetAliasMappingModalProps> = ({
    isOpen,
    onClose,
    unrecognizedTicker,
    onAliasCreated,
}) => {
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const debouncedSearchTerm = useDebounce(searchTerm, 300);
    const { data: searchResults, isLoading, error } = useAssetSearch(debouncedSearchTerm);

    const handleSave = () => {
        if (selectedAsset) {
            onAliasCreated({
                alias_symbol: unrecognizedTicker,
                asset_id: selectedAsset.id,
                source: `import_mapping_${unrecognizedTicker}`,
            });
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
                <h3 className="font-bold text-lg">Map Unrecognized Symbol</h3>
                <p className="py-4">
                    The symbol <span className="font-mono bg-gray-200 px-1 rounded">{unrecognizedTicker}</span> was not found.
                    Search for an existing asset to map it to.
                </p>

                <div className="form-control w-full">
                    <label className="label">
                        <span className="label-text">Search for Asset</span>
                    </label>
                    <input
                        type="text"
                        placeholder="Type to search by name or ticker..."
                        className="input input-bordered w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                {isLoading && <span className="loading loading-spinner loading-sm"></span>}

                {error && <p className="text-red-500 text-xs mt-1">{error.message}</p>}

                {searchResults && searchResults.length > 0 && (
                    <ul className="menu bg-base-100 w-full rounded-box mt-2 border max-h-60 overflow-y-auto">
                        {searchResults.map((asset) => (
                            <li key={asset.id} onClick={() => {
                                setSelectedAsset(asset);
                                setSearchTerm(`${asset.name} (${asset.ticker_symbol})`);
                            }}>
                                <a>{asset.name} ({asset.ticker_symbol})</a>
                            </li>
                        ))}
                    </ul>
                )}

                {debouncedSearchTerm && !isLoading && searchResults?.length === 0 && (
                     <p className="text-sm text-gray-500 mt-2">No assets found.</p>
                )}


                <div className="modal-action">
                    <button onClick={onClose} className="btn btn-ghost">Cancel</button>
                    <button onClick={handleSave} className="btn btn-primary" disabled={!selectedAsset}>
                        Save Mapping
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AssetAliasMappingModal;

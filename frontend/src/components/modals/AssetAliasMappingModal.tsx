import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAssetSearch } from '../../hooks/usePortfolio';
import { searchMutualFunds } from '../../services/assetApi';
import { createAsset, AssetCreationPayload } from '../../services/portfolioApi';
import { Asset, MutualFundSearchResult } from '../../types/asset';

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

// Hook for MF search
const useMfSearch = (query: string) => {
    return useQuery({
        queryKey: ['mfSearch', query],
        queryFn: () => searchMutualFunds(query),
        enabled: query.length >= 3,
    });
};

interface AssetAliasMappingModalProps {
    isOpen: boolean;
    onClose: () => void;
    unrecognizedTicker: string;
    portfolioId: string;
    source: string;
    onAliasCreated: (alias: { alias_symbol: string; asset_id: string, source: string }) => void;
}

const AssetAliasMappingModal: React.FC<AssetAliasMappingModalProps> = ({
    isOpen,
    onClose,
    unrecognizedTicker,
    source,
    onAliasCreated,
}) => {
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [selectedMf, setSelectedMf] = useState<MutualFundSearchResult | null>(null);
    const [isAssetSelected, setIsAssetSelected] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const debouncedSearchTerm = useDebounce(searchTerm, 300);

    const isMfSource = source.includes('MFCentral');
    const queryClient = useQueryClient();

    // Use different search based on source type
    const { data: assetResults, isLoading: isLoadingAssets, error: assetError } = useAssetSearch(
        isMfSource ? '' : debouncedSearchTerm  // Only search assets for non-MF sources
    );
    const { data: mfResults, isLoading: isLoadingMf, error: mfError } = useMfSearch(
        isMfSource ? debouncedSearchTerm : ''  // Only search MF for MF sources
    );

    const searchResults = isMfSource ? mfResults : assetResults;
    const isLoading = isMfSource ? isLoadingMf : isLoadingAssets;
    const error = isMfSource ? mfError : assetError;

    // Mutation to create MF asset
    const createAssetMutation = useMutation({
        mutationFn: (payload: AssetCreationPayload) => createAsset(payload),
        onSuccess: (newAsset) => {
            queryClient.invalidateQueries({ queryKey: ['assetSearch'] });
            onAliasCreated({
                alias_symbol: unrecognizedTicker,
                asset_id: newAsset.id,
                source: source,
            });
            onClose();
        },
    });

    const handleSave = () => {
        if (isMfSource && selectedMf) {
            // For MF sources, create the asset first
            createAssetMutation.mutate({
                ticker_symbol: selectedMf.ticker_symbol,
                name: selectedMf.name,
                asset_type: 'Mutual Fund',
                currency: 'INR',  // Indian MFs are in INR
            });
        } else if (selectedAsset) {
            // For regular assets, just create the alias
            onAliasCreated({
                alias_symbol: unrecognizedTicker,
                asset_id: selectedAsset.id,
                source: source,
            });
            onClose();
        }
    };

    // Reset state when modal opens/closes
    useEffect(() => {
        if (!isOpen) {
            setSearchTerm('');
            setSelectedAsset(null);
            setSelectedMf(null);
            setIsAssetSelected(false);
        }
    }, [isOpen]);

    if (!isOpen) return null;

    const canSave = isMfSource ? (selectedMf && isAssetSelected) : (selectedAsset && isAssetSelected);

    return (
        <div className="modal modal-open">
            <div className="modal-box">
                <h3 className="font-bold text-lg">Map Unrecognized Symbol</h3>
                <p className="py-4">
                    <span className="font-mono bg-gray-200 px-1 rounded text-sm break-all">{unrecognizedTicker}</span>
                    <span className="block mt-2">Search for an existing asset to map it to.</span>
                    {isMfSource && <span className="text-xs text-blue-600 block mt-1">Searching AMFI Mutual Fund database</span>}
                </p>

                <div className="form-control w-full">
                    <label className="label">
                        <span className="label-text">{isMfSource ? 'Search Mutual Funds' : 'Search Assets'}</span>
                    </label>
                    <input
                        type="text"
                        placeholder={isMfSource ? "Type at least 3 characters to search MF..." : "Type to search by name or ticker..."}
                        className="input input-bordered w-full"
                        value={searchTerm}
                        onChange={(e) => {
                            setSearchTerm(e.target.value);
                            setSelectedAsset(null);
                            setSelectedMf(null);
                            setIsAssetSelected(false);
                        }}
                    />
                </div>

                {isLoading && <span className="loading loading-spinner loading-sm mt-2"></span>}

                {error && <p className="text-red-500 text-xs mt-1">{error.message}</p>}

                {createAssetMutation.isError && (
                    <p className="text-red-500 text-xs mt-1">
                        Failed to create asset: {(createAssetMutation.error as Error).message}
                    </p>
                )}

                {searchResults && searchResults.length > 0 && !isAssetSelected && (
                    <ul className="menu bg-base-100 w-full rounded-box mt-2 border max-h-60 overflow-y-auto">
                        {isMfSource ? (
                            (searchResults as MutualFundSearchResult[]).map((mf, index) => (
                                <li key={index} onClick={() => {
                                    setSelectedMf(mf);
                                    setSearchTerm(`${mf.name}`);
                                    setIsAssetSelected(true);
                                }}>
                                    <a className="text-sm">
                                        <span className="truncate">{mf.name}</span>
                                        <span className="text-xs text-gray-500">({mf.ticker_symbol})</span>
                                    </a>
                                </li>
                            ))
                        ) : (
                            (searchResults as Asset[]).map((asset) => (
                                <li key={asset.id} onClick={() => {
                                    setSelectedAsset(asset);
                                    setSearchTerm(`${asset.name} (${asset.ticker_symbol})`);
                                    setIsAssetSelected(true);
                                }}>
                                    <a>{asset.name} ({asset.ticker_symbol})</a>
                                </li>
                            ))
                        )}
                    </ul>
                )}

                {debouncedSearchTerm && debouncedSearchTerm.length >= (isMfSource ? 3 : 1) && !isLoading && !isAssetSelected && searchResults?.length === 0 && (
                    <p className="text-sm text-gray-500 mt-2">No {isMfSource ? 'mutual funds' : 'assets'} found.</p>
                )}


                <div className="modal-action">
                    <button onClick={onClose} className="btn btn-ghost" disabled={createAssetMutation.isPending}>Cancel</button>
                    <button
                        onClick={handleSave}
                        className="btn btn-primary"
                        disabled={!canSave || createAssetMutation.isPending}
                    >
                        {createAssetMutation.isPending ? 'Creating...' : (isMfSource ? 'Create Asset & Alias' : 'Create Alias')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AssetAliasMappingModal;


import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAssetSearch } from '../../hooks/usePortfolio';
import { searchMutualFunds } from '../../services/assetApi';
import { createAsset, lookupAsset, AssetCreationPayload } from '../../services/portfolioApi';
import { Asset, MutualFundSearchResult } from '../../types/asset';
import { useDebounce } from '../../hooks/useDebounce';

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

    const isMfSource = source.includes('MFCentral') || source.includes('CAMS') || source.includes('Zerodha Coin') || source.includes('KFintech') || source.includes('ICICI Securities');
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

    // Mutation to create MF asset (or use existing if 409)
    const createAssetMutation = useMutation({
        mutationFn: async (payload: AssetCreationPayload) => {
            try {
                return await createAsset(payload);
            } catch (err: unknown) {
                // If asset already exists (409), lookup by ticker symbol
                const error = err as { response?: { status?: number } };
                if (error.response?.status === 409) {
                    // Use the lookupAsset API which handles auth properly
                    // lookupAsset returns an array
                    const existingAssets = await lookupAsset(payload.ticker_symbol);
                    if (existingAssets && existingAssets.length > 0) {
                        return existingAssets[0];
                    }
                }
                throw err;
            }
        },
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
            // For MF sources, create the asset first (or use existing)
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
        <div className="modal-overlay pt-safe pb-safe p-4" onClick={onClose} style={{ zIndex: 1000 }}>
            <div className="modal-content relative w-full max-w-lg flex flex-col pt-safe bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden border border-gray-200 dark:border-gray-700" onClick={(e) => e.stopPropagation()}>
                <div className="p-6">
                    <h3 className="font-bold text-lg dark:text-gray-100">Map Unrecognized Symbol</h3>
                    <p className="py-4">
                        <span className="font-mono bg-gray-200 dark:bg-gray-600 dark:text-gray-200 px-1 rounded text-sm break-all">{unrecognizedTicker}</span>
                        <span className="block mt-2 text-gray-600 dark:text-gray-400">Search for an existing asset to map it to.</span>
                        {isMfSource && <span className="text-xs text-blue-600 dark:text-blue-400 block mt-1">Searching AMFI Mutual Fund database</span>}
                    </p>

                    <div className="form-control w-full">
                        <label className="label">
                            <span className="label-text dark:text-gray-300">{isMfSource ? 'Search Mutual Funds' : 'Search Assets'}</span>
                        </label>
                        <input
                            type="text"
                            placeholder={isMfSource ? "Type at least 3 characters to search MF..." : "Type to search by name or ticker..."}
                            className="input input-bordered w-full dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
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
                        <ul className="menu bg-base-100 dark:bg-gray-700 w-full rounded-box mt-2 border border-gray-200 dark:border-gray-600 max-h-60 overflow-y-auto">
                            {isMfSource ? (
                                (searchResults as MutualFundSearchResult[]).map((mf, index) => (
                                    <li key={index} onClick={() => {
                                        setSelectedMf(mf);
                                        setSearchTerm(`${mf.name}`);
                                        setIsAssetSelected(true);
                                    }}>
                                        <a className="text-sm dark:text-gray-200">
                                            <span className="truncate">{mf.name}</span>
                                            <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">({mf.ticker_symbol})</span>
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
                                        <a className="text-sm dark:text-gray-200">{asset.name} ({asset.ticker_symbol})</a>
                                    </li>
                                ))
                            )}
                        </ul>
                    )}

                    {debouncedSearchTerm && debouncedSearchTerm.length >= (isMfSource ? 3 : 1) && !isLoading && !isAssetSelected && searchResults?.length === 0 && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">No {isMfSource ? 'mutual funds' : 'assets'} found.</p>
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
        </div>
    );
};

export default AssetAliasMappingModal;


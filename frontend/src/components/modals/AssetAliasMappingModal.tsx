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
        <div className="modal-overlay">
            <div className="modal-content max-w-md p-6">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="font-bold text-lg">Map Unrecognized Symbol</h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        disabled={createAssetMutation.isPending}
                        aria-label="Close"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                
                <p className="py-2">
                    <span className="font-mono bg-gray-200 dark:bg-gray-600 dark:text-gray-200 px-1 rounded text-sm break-all">{unrecognizedTicker}</span>
                    <span className="block mt-2">Search for an existing asset to map it to.</span>
                    {isMfSource && <span className="text-xs text-blue-600 dark:text-blue-400 block mt-1">Searching AMFI Mutual Fund database</span>}
                </p>

                <div className="form-group w-full mt-4">
                    <label className="form-label">
                        {isMfSource ? 'Search Mutual Funds' : 'Search Assets'}
                    </label>
                    <input
                        type="text"
                        placeholder={isMfSource ? "Type at least 3 characters to search MF..." : "Type to search by name or ticker..."}
                        className="form-input"
                        value={searchTerm}
                        onChange={(e) => {
                            setSearchTerm(e.target.value);
                            setSelectedAsset(null);
                            setSelectedMf(null);
                            setIsAssetSelected(false);
                        }}
                    />
                </div>

                {isLoading && <div className="flex justify-center mt-2"><span className="loading loading-spinner loading-sm"></span></div>}

                {error && <p className="text-red-500 text-xs mt-1">{error.message}</p>}

                {createAssetMutation.isError && (
                    <p className="text-red-500 text-xs mt-1">
                        Failed to create asset: {(createAssetMutation.error as Error).message}
                    </p>
                )}

                {searchResults && searchResults.length > 0 && !isAssetSelected && (
                    <ul className="bg-white dark:bg-gray-700 w-full rounded-md mt-2 border dark:border-gray-600 max-h-60 overflow-y-auto divide-y dark:divide-gray-600 shadow-lg">
                        {isMfSource ? (
                            (searchResults as MutualFundSearchResult[]).map((mf, index) => (
                                <li key={index} onClick={() => {
                                    setSelectedMf(mf);
                                    setSearchTerm(`${mf.name}`);
                                    setIsAssetSelected(true);
                                }} className="p-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                                    <div className="text-sm">
                                        <div className="font-medium truncate">{mf.name}</div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400">({mf.ticker_symbol})</div>
                                    </div>
                                </li>
                            ))
                        ) : (
                            (searchResults as Asset[]).map((asset) => (
                                <li key={asset.id} onClick={() => {
                                    setSelectedAsset(asset);
                                    setSearchTerm(`${asset.name} (${asset.ticker_symbol})`);
                                    setIsAssetSelected(true);
                                }} className="p-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                                    <div className="text-sm font-medium">{asset.name} ({asset.ticker_symbol})</div>
                                </li>
                            ))
                        )}
                    </ul>
                )}

                {debouncedSearchTerm && debouncedSearchTerm.length >= (isMfSource ? 3 : 1) && !isLoading && !isAssetSelected && searchResults?.length === 0 && (
                    <p className="text-sm text-gray-500 mt-2">No {isMfSource ? 'mutual funds' : 'assets'} found.</p>
                )}


                <div className="flex justify-end gap-3 mt-8">
                    <button onClick={onClose} className="btn btn-secondary" disabled={createAssetMutation.isPending}>Cancel</button>
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

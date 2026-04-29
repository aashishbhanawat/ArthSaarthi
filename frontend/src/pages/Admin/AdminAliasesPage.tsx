import React, { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    getAliases,
    createAlias,
    updateAlias,
    deleteAlias,
    AssetAliasWithAsset,
    AssetAliasCreate,
    AssetAliasUpdate,
} from '../../services/adminApi';
import apiClient from '../../services/api';
import { AxiosError } from 'axios';
import { DeleteConfirmationModal } from '../../components/common/DeleteConfirmationModal';
import { useToast } from '../../context/ToastContext';
import { PencilIcon, TrashIcon, PlusIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

interface LocalAsset {
    id: string;
    ticker_symbol: string;
    name: string;
    asset_type: string;
}

const PAGE_SIZE = 50;

const AdminAliasesPage: React.FC = () => {
    const queryClient = useQueryClient();
    const { addToast } = useToast();

    // --- Search & Pagination ---
    const [searchInput, setSearchInput] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [page, setPage] = useState(0);

    // Debounce search input
    useEffect(() => {
        const timer = setTimeout(() => {
            setSearchQuery(searchInput);
            setPage(0); // Reset to first page on new search
        }, 300);
        return () => clearTimeout(timer);
    }, [searchInput]);

    const { data, isLoading, isError } = useQuery({
        queryKey: ['adminAliases', searchQuery, page],
        queryFn: () => getAliases({
            q: searchQuery || undefined,
            skip: page * PAGE_SIZE,
            limit: PAGE_SIZE,
        }),
    });

    const aliases = data?.items ?? [];
    const totalCount = data?.total ?? 0;
    const totalPages = Math.ceil(totalCount / PAGE_SIZE);

    // --- Form Modal State ---
    const [isFormOpen, setFormOpen] = useState(false);
    const [editingAlias, setEditingAlias] = useState<AssetAliasWithAsset | null>(null);
    const [formData, setFormData] = useState({ alias_symbol: '', source: '', asset_id: '' });

    // --- Asset Search ---
    const [assetQuery, setAssetQuery] = useState('');
    const [assetResults, setAssetResults] = useState<LocalAsset[]>([]);
    const [selectedAsset, setSelectedAsset] = useState<LocalAsset | null>(null);
    const [showDropdown, setShowDropdown] = useState(false);

    // --- Delete Modal State ---
    const [isDeleteOpen, setDeleteOpen] = useState(false);
    const [deletingAlias, setDeletingAlias] = useState<AssetAliasWithAsset | null>(null);

    // Asset search with debounce
    const searchAssets = useCallback(async (query: string) => {
        if (query.length < 2) {
            setAssetResults([]);
            return;
        }
        try {
            const response = await apiClient.get<LocalAsset[]>('/api/v1/admin/assets/search-local', {
                params: { query, limit: 10 },
            });
            setAssetResults(response.data);
            setShowDropdown(true);
        } catch {
            setAssetResults([]);
        }
    }, []);

    useEffect(() => {
        const timer = setTimeout(() => searchAssets(assetQuery), 300);
        return () => clearTimeout(timer);
    }, [assetQuery, searchAssets]);

    // Mutations
    const createMutation = useMutation({
        mutationFn: (d: AssetAliasCreate) => createAlias(d),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['adminAliases'] });
            addToast('Alias created successfully.', 'success');
            closeForm();
        },
        onError: (err: AxiosError<{ detail?: string }>) => {
            addToast(err.response?.data?.detail || 'Failed to create alias.', 'error');
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, d }: { id: string; d: AssetAliasUpdate }) => updateAlias(id, d),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['adminAliases'] });
            addToast('Alias updated successfully.', 'success');
            closeForm();
        },
        onError: (err: AxiosError<{ detail?: string }>) => {
            addToast(err.response?.data?.detail || 'Failed to update alias.', 'error');
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => deleteAlias(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['adminAliases'] });
            addToast('Alias deleted.', 'success');
            setDeleteOpen(false);
            setDeletingAlias(null);
        },
        onError: () => {
            addToast('Failed to delete alias.', 'error');
        },
    });

    // Handlers
    const openCreateForm = () => {
        setEditingAlias(null);
        setFormData({ alias_symbol: '', source: '', asset_id: '' });
        setSelectedAsset(null);
        setAssetQuery('');
        setFormOpen(true);
    };

    const openEditForm = (alias: AssetAliasWithAsset) => {
        setEditingAlias(alias);
        setFormData({
            alias_symbol: alias.alias_symbol,
            source: alias.source,
            asset_id: alias.asset_id,
        });
        setSelectedAsset({
            id: alias.asset_id,
            ticker_symbol: alias.asset_ticker,
            name: alias.asset_name,
            asset_type: '',
        });
        setAssetQuery(`${alias.asset_ticker} — ${alias.asset_name}`);
        setFormOpen(true);
    };

    const closeForm = () => {
        setFormOpen(false);
        setEditingAlias(null);
        setAssetResults([]);
        setShowDropdown(false);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.alias_symbol || !formData.source || !formData.asset_id) {
            addToast('Please fill all fields and select an asset.', 'error');
            return;
        }
        if (editingAlias) {
            updateMutation.mutate({ id: editingAlias.id, d: formData });
        } else {
            createMutation.mutate(formData);
        }
    };

    const selectAsset = (asset: LocalAsset) => {
        setSelectedAsset(asset);
        setFormData({ ...formData, asset_id: asset.id });
        setAssetQuery(`${asset.ticker_symbol} — ${asset.name}`);
        setShowDropdown(false);
    };

    const isSaving = createMutation.isPending || updateMutation.isPending;

    return (
        <div className="container mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">Symbol Aliases</h1>
                <button onClick={openCreateForm} className="btn btn-primary flex items-center gap-2">
                    <PlusIcon className="h-5 w-5" />
                    Add Alias
                </button>
            </div>

            {/* Search Bar */}
            <div className="mb-4 relative">
                <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    className="input w-full pl-11"
                    placeholder="Search by alias, source, ticker, or asset name..."
                />
                {totalCount > 0 && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                        {totalCount.toLocaleString()} result{totalCount !== 1 ? 's' : ''}
                    </span>
                )}
            </div>

            {isLoading && <p>Loading aliases...</p>}
            {isError && <p className="text-red-500">Error fetching aliases.</p>}
            {!isLoading && !isError && (
                <div className="card overflow-x-auto">
                    {aliases.length === 0 ? (
                        <p className="text-gray-500 p-4 text-center">
                            {searchQuery
                                ? `No aliases matching "${searchQuery}".`
                                : 'No symbol aliases found. Create one to map unrecognized tickers to known assets.'}
                        </p>
                    ) : (
                        <>
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                <thead className="bg-gray-50 dark:bg-gray-700">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Alias Symbol</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Source</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Maps To (Ticker)</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Asset Name</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                    {aliases.map((alias) => (
                                        <tr key={alias.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                            <td className="px-4 py-3 whitespace-nowrap font-mono text-sm">{alias.alias_symbol}</td>
                                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">{alias.source}</td>
                                            <td className="px-4 py-3 whitespace-nowrap font-mono text-sm text-blue-600 dark:text-blue-400">{alias.asset_ticker}</td>
                                            <td className="px-4 py-3 text-sm">{alias.asset_name}</td>
                                            <td className="px-4 py-3 whitespace-nowrap text-right">
                                                <button onClick={() => openEditForm(alias)} className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mr-3" title="Edit">
                                                    <PencilIcon className="h-4 w-4 inline" />
                                                </button>
                                                <button onClick={() => { setDeletingAlias(alias); setDeleteOpen(true); }} className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300" title="Delete">
                                                    <TrashIcon className="h-4 w-4 inline" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-between px-4 py-3 border-t dark:border-gray-700">
                                    <span className="text-sm text-gray-500 dark:text-gray-400">
                                        Page {page + 1} of {totalPages}
                                    </span>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setPage(p => Math.max(0, p - 1))}
                                            disabled={page === 0}
                                            className="btn btn-secondary btn-sm disabled:opacity-50"
                                        >
                                            Previous
                                        </button>
                                        <button
                                            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                                            disabled={page >= totalPages - 1}
                                            className="btn btn-secondary btn-sm disabled:opacity-50"
                                        >
                                            Next
                                        </button>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}

            {/* Form Modal */}
            {isFormOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={closeForm}>
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4 p-6" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-xl font-bold mb-4">{editingAlias ? 'Edit Alias' : 'Create Alias'}</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Alias Symbol</label>
                                <input
                                    type="text"
                                    value={formData.alias_symbol}
                                    onChange={(e) => setFormData({ ...formData, alias_symbol: e.target.value })}
                                    className="input w-full"
                                    placeholder="e.g. HDFCAMC-EQ"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">Source</label>
                                <input
                                    type="text"
                                    value={formData.source}
                                    onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                                    className="input w-full"
                                    placeholder="e.g. Zerodha Tradebook, ICICI Direct"
                                    required
                                />
                            </div>
                            <div className="relative">
                                <label className="block text-sm font-medium mb-1">Target Asset</label>
                                <input
                                    type="text"
                                    value={assetQuery}
                                    onChange={(e) => {
                                        setAssetQuery(e.target.value);
                                        setSelectedAsset(null);
                                        setFormData({ ...formData, asset_id: '' });
                                    }}
                                    onFocus={() => assetResults.length > 0 && setShowDropdown(true)}
                                    className="input w-full"
                                    placeholder="Search by ticker or name..."
                                    required
                                />
                                {showDropdown && assetResults.length > 0 && (
                                    <ul className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-700 border dark:border-gray-600 rounded-md shadow-lg max-h-48 overflow-auto">
                                        {assetResults.map((asset) => (
                                            <li
                                                key={asset.id}
                                                className="px-3 py-2 cursor-pointer hover:bg-blue-100 dark:hover:bg-gray-600 text-sm"
                                                onClick={() => selectAsset(asset)}
                                            >
                                                <span className="font-mono font-semibold">{asset.ticker_symbol}</span>
                                                <span className="text-gray-500 dark:text-gray-400 ml-2">— {asset.name}</span>
                                                <span className="text-xs text-gray-400 dark:text-gray-500 ml-2">({asset.asset_type})</span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                                {selectedAsset && (
                                    <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                                        ✓ Selected: {selectedAsset.ticker_symbol}
                                    </p>
                                )}
                            </div>
                            <div className="flex justify-end gap-3 pt-2">
                                <button type="button" onClick={closeForm} className="btn btn-secondary">Cancel</button>
                                <button type="submit" className="btn btn-primary" disabled={isSaving || !formData.asset_id}>
                                    {isSaving ? 'Saving...' : editingAlias ? 'Update' : 'Create'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Delete Confirmation */}
            {deletingAlias && (
                <DeleteConfirmationModal
                    isOpen={isDeleteOpen}
                    onClose={() => { setDeleteOpen(false); setDeletingAlias(null); }}
                    onConfirm={() => deleteMutation.mutate(deletingAlias.id)}
                    title="Delete Alias"
                    message={`Are you sure you want to delete the alias "${deletingAlias.alias_symbol}" (source: ${deletingAlias.source})?`}
                    isDeleting={deleteMutation.isPending}
                />
            )}
        </div>
    );
};

export default AdminAliasesPage;

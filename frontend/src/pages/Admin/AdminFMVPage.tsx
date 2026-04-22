import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '../../context/ToastContext';

interface Asset {
    id: string;
    ticker_symbol: string;
    name: string;
    asset_type: string;
    isin?: string;
    fmv_2018: number | null;
}

const fetchAssets = async (search: string): Promise<Asset[]> => {
    // Use local-only admin search for FMV management
    const url = `/api/v1/admin/assets/fmv-search?query=${encodeURIComponent(search)}&limit=50`;
    const response = await fetch(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    });
    if (!response.ok) throw new Error('Failed to fetch assets');
    return response.json();
};

const updateFMV2018 = async ({
    ticker,
    fmv_2018,
}: {
    ticker: string;
    fmv_2018: number;
}) => {
    const response = await fetch(`/api/v1/admin/assets/${ticker}/fmv-2018`, {
        method: 'PATCH',
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fmv_2018 }),
    });
    if (!response.ok) throw new Error('Failed to update FMV');
    return response.json();
};

const lookupFMV2018 = async (ticker: string) => {
    const response = await fetch(
        `/api/v1/admin/assets/${ticker}/fmv-2018/lookup`,
        {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        }
    );
    if (!response.ok) throw new Error('Lookup failed');
    return response.json();
};

const AdminFMVPage: React.FC = () => {
    const { addToast } = useToast();
    const queryClient = useQueryClient();
    const [search, setSearch] = useState('');
    const [editingTicker, setEditingTicker] = useState<string | null>(null);
    const [editValue, setEditValue] = useState('');
    const [fetchingTicker, setFetchingTicker] = useState<string | null>(null);

    const { data: assets = [], isLoading } = useQuery({
        queryKey: ['assets-fmv', search],
        queryFn: () => fetchAssets(search),
        staleTime: 30000,
    });

    const updateMutation = useMutation({
        mutationFn: updateFMV2018,
        onSuccess: (_, variables) => {
            addToast(`FMV 2018 updated for ${variables.ticker}`, 'success');
            queryClient.invalidateQueries({ queryKey: ['assets-fmv'] });
            setEditingTicker(null);
        },
        onError: () => {
            addToast('Failed to update FMV', 'error');
        },
    });

    const handleEdit = (ticker: string, currentValue: number | null) => {
        setEditingTicker(ticker);
        setEditValue(currentValue?.toString() || '');
    };

    const handleSave = (ticker: string) => {
        const value = parseFloat(editValue);
        if (isNaN(value) || value <= 0) {
            addToast('Please enter a valid positive number', 'error');
            return;
        }
        updateMutation.mutate({ ticker, fmv_2018: value });
    };

    const handleCancel = () => {
        setEditingTicker(null);
        setEditValue('');
    };

    const handleFetch = async (ticker: string) => {
        setFetchingTicker(ticker);
        try {
            const result = await lookupFMV2018(ticker);
            if (result.fmv_2018) {
                // Auto-save the fetched value
                updateMutation.mutate({ ticker, fmv_2018: result.fmv_2018 });
                addToast(result.message, 'success');
            } else {
                addToast(result.message || 'No data found', 'error');
            }
        } catch {
            addToast('Failed to fetch FMV from Yahoo Finance', 'error');
        } finally {
            setFetchingTicker(null);
        }
    };

    const [isSeeding, setIsSeeding] = useState(false);
    const [overwriteSeed, setOverwriteSeed] = useState(false);

    const handleBulkSeed = async () => {
        setIsSeeding(true);
        try {
            const response = await fetch('/api/v1/admin/assets/fmv-2018/seed', {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ overwrite: overwriteSeed }),
            });
            if (!response.ok) throw new Error('Seed failed');
            const result = await response.json();
            addToast(
                `${result.message} (${result.skipped} skipped, ${result.errors} errors)`,
                'success'
            );
            queryClient.invalidateQueries({ queryKey: ['assets-fmv'] });
        } catch {
            addToast('Bulk seed failed. Check server logs.', 'error');
        } finally {
            setIsSeeding(false);
        }
    };

    // Filter to only show equity-type assets
    const equityAssets = assets.filter(
        (a) =>
            a.asset_type?.toUpperCase() === 'STOCK' ||
            a.asset_type?.toUpperCase() === 'ETF' ||
            a.asset_type?.toUpperCase()?.includes('MUTUAL')
    );

    return (
        <div className="container mx-auto">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h1 className="text-3xl font-bold dark:text-white">
                        FMV 2018 Management
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                        Set Fair Market Value as of Jan 31, 2018 for capital gains
                        grandfathering (Section 112A).
                    </p>
                </div>
                <button
                    onClick={handleBulkSeed}
                    disabled={isSeeding}
                    className="btn btn-primary"
                    title="Download BSE/AMFI data and populate FMV for all assets"
                >
                    {isSeeding ? 'Seeding...' : 'Seed from BSE/AMFI'}
                </button>
            </div>

            <div className="mb-6 flex items-center gap-2">
                <input
                    type="checkbox"
                    id="overwrite"
                    checked={overwriteSeed}
                    onChange={(e) => setOverwriteSeed(e.target.checked)}
                    className="form-checkbox h-4 w-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                />
                <label htmlFor="overwrite" className="text-sm text-gray-700 dark:text-gray-300">
                    Overwrite existing values (Use official BSE/AMFI prices instead of Yahoo estimates)
                </label>
            </div>

            {/* Search */}
            <div className="mb-4">
                <input
                    type="text"
                    placeholder="Search assets by ticker or name..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="form-input w-full max-w-md"
                />
            </div>

            {/* Table */}
            <div className="card overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b dark:border-gray-700">
                            <th className="text-left p-3">Ticker</th>
                            <th className="text-left p-3">ISIN</th>
                            <th className="text-left p-3">Name</th>
                            <th className="text-left p-3">Type</th>
                            <th className="text-right p-3">FMV (Jan 31, 2018)</th>
                            <th className="text-center p-3">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading && (
                            <tr>
                                <td colSpan={5} className="text-center p-8">
                                    Loading...
                                </td>
                            </tr>
                        )}
                        {!isLoading && equityAssets.length === 0 && (
                            <tr>
                                <td
                                    colSpan={5}
                                    className="text-center p-8 text-gray-500"
                                >
                                    No equity assets found. Search by ticker.
                                </td>
                            </tr>
                        )}
                        {equityAssets.map((asset) => (
                            <tr
                                key={asset.id || asset.ticker_symbol}
                                className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                            >
                                <td className="p-3 font-mono">
                                    {asset.ticker_symbol}
                                </td>
                                <td className="p-3 font-mono text-xs text-gray-500">
                                    {asset.isin || <span className="text-red-400">Missing</span>}
                                </td>
                                <td className="p-3">{asset.name}</td>
                                <td className="p-3">{asset.asset_type}</td>
                                <td className="p-3 text-right">
                                    {editingTicker === asset.ticker_symbol ? (
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={editValue}
                                            onChange={(e) =>
                                                setEditValue(e.target.value)
                                            }
                                            className="form-input w-32 text-right"
                                            autoFocus
                                        />
                                    ) : (
                                        <span
                                            className={
                                                asset.fmv_2018
                                                    ? 'text-green-600 dark:text-green-400'
                                                    : 'text-gray-400'
                                            }
                                        >
                                            {asset.fmv_2018
                                                ? `₹${asset.fmv_2018.toFixed(2)}`
                                                : 'Not set'}
                                        </span>
                                    )}
                                </td>
                                <td className="p-3 text-center">
                                    {editingTicker === asset.ticker_symbol ? (
                                        <div className="flex gap-2 justify-center">
                                            <button
                                                onClick={() =>
                                                    handleSave(
                                                        asset.ticker_symbol
                                                    )
                                                }
                                                disabled={updateMutation.isPending}
                                                className="btn btn-primary btn-sm"
                                            >
                                                {updateMutation.isPending
                                                    ? 'Saving...'
                                                    : 'Save'}
                                            </button>
                                            <button
                                                onClick={handleCancel}
                                                className="btn btn-secondary btn-sm"
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="flex gap-2 justify-center">
                                            {!asset.fmv_2018 && (
                                                <button
                                                    onClick={() =>
                                                        handleFetch(
                                                            asset.ticker_symbol
                                                        )
                                                    }
                                                    disabled={
                                                        fetchingTicker ===
                                                        asset.ticker_symbol
                                                    }
                                                    className="btn btn-primary btn-sm"
                                                    title="Fetch from Yahoo Finance"
                                                >
                                                    {fetchingTicker ===
                                                        asset.ticker_symbol
                                                        ? 'Fetching...'
                                                        : 'Fetch'}
                                                </button>
                                            )}
                                            <button
                                                onClick={() =>
                                                    handleEdit(
                                                        asset.ticker_symbol,
                                                        asset.fmv_2018
                                                    )
                                                }
                                                className="btn btn-secondary btn-sm"
                                            >
                                                Edit
                                            </button>
                                        </div>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Help text */}
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <h3 className="font-semibold text-blue-900 dark:text-blue-300">
                    About FMV 2018
                </h3>
                <p className="text-sm text-blue-800 dark:text-blue-400 mt-1">
                    The Fair Market Value (FMV) as of January 31, 2018 is used
                    for grandfathering under Section 112A. For listed equity
                    acquired before Feb 1, 2018, gains are calculated using:
                </p>
                <code className="block mt-2 p-2 bg-white dark:bg-gray-800 rounded text-sm">
                    Cost = Max(Actual Cost, Min(FMV, Sale Price))
                </code>
            </div>
        </div>
    );
};

export default AdminFMVPage;

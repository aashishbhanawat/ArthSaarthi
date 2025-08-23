import React from 'react';
import { Watchlist } from '../../types/watchlist';
import { usePortfolioAssets } from '../../hooks/usePortfolios';
import { useRemoveWatchlistItem } from '../../hooks/useWatchlists';
import { TrashIcon } from '@heroicons/react/24/outline';

interface Props {
    watchlist: Watchlist | null;
}

const WatchlistTable: React.FC<Props> = ({ watchlist }) => {
    const { data: assets, isLoading, isError } = usePortfolioAssets(watchlist?.id);
    const removeMutation = useRemoveWatchlistItem();

    const handleRemove = (itemId: string) => {
        if (watchlist) {
            removeMutation.mutate({ watchlistId: watchlist.id, itemId });
        }
    };

    if (!watchlist) {
        return <p>Select a watchlist to see the assets.</p>;
    }

    if (isLoading) return <p>Loading assets...</p>;
    if (isError) return <p>Error loading assets.</p>;

    return (
        <div>
            <h2 className="text-xl font-bold mb-2">{watchlist.name}</h2>
            <table className="min-w-full bg-white">
                <thead>
                    <tr>
                        <th className="py-2">Ticker</th>
                        <th className="py-2">Name</th>
                        <th className="py-2">Price</th>
                        <th className="py-2">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {assets?.map((asset) => (
                        <tr key={asset.id}>
                            <td className="border px-4 py-2">{asset.ticker_symbol}</td>
                            <td className="border px-4 py-2">{asset.name}</td>
                            <td className="border px-4 py-2">{asset.current_price}</td>
                            <td className="border px-4 py-2">
                                <button onClick={() => handleRemove(asset.id)} className="text-red-500 hover:text-red-700">
                                    <TrashIcon className="h-5 w-5" />
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default WatchlistTable;

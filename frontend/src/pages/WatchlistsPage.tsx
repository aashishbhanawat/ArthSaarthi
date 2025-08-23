import React, { useState } from 'react';
import WatchlistSelector from '../components/Watchlists/WatchlistSelector';
import WatchlistTable from '../components/Watchlists/WatchlistTable';
import { Watchlist } from '../types/watchlist';

const WatchlistsPage: React.FC = () => {
    const [selectedWatchlist, setSelectedWatchlist] = useState<Watchlist | null>(null);

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">Watchlists</h1>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <WatchlistSelector onSelectWatchlist={setSelectedWatchlist} />
                </div>
                <div className="md:col-span-2">
                    <WatchlistTable watchlist={selectedWatchlist} />
                </div>
            </div>
        </div>
    );
};

export default WatchlistsPage;

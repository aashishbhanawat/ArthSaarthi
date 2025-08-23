import React from 'react';
import { useWatchlists } from '../../hooks/useWatchlists';
import { Watchlist } from '../../types/watchlist';

interface Props {
    onSelectWatchlist: (watchlist: Watchlist) => void;
}

const WatchlistSelector: React.FC<Props> = ({ onSelectWatchlist }) => {
    const { data: watchlists, isLoading, isError } = useWatchlists();

    if (isLoading) return <p>Loading watchlists...</p>;
    if (isError) return <p>Error loading watchlists.</p>;

    return (
        <div>
            <h2 className="text-xl font-bold mb-2">My Watchlists</h2>
            <ul>
                {watchlists?.map((watchlist) => (
                    <li key={watchlist.id} onClick={() => onSelectWatchlist(watchlist)} className="cursor-pointer p-2 hover:bg-gray-200">
                        {watchlist.name}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default WatchlistSelector;

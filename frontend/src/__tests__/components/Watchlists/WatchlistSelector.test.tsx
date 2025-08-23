import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider, UseQueryResult } from '@tanstack/react-query';
import WatchlistSelector from '../../../components/Watchlists/WatchlistSelector';
import * as useWatchlists from '../../../hooks/useWatchlists';
import { Watchlist } from '../../../types/watchlist';

const queryClient = new QueryClient();

const mockWatchlists: Watchlist[] = [
    { id: '1', name: 'Tech Stocks', user_id: '1', items: [] },
    { id: '2', name: 'Crypto', user_id: '1', items: [] },
];

describe('WatchlistSelector', () => {
    beforeEach(() => {
        jest.spyOn(useWatchlists, 'useWatchlists').mockReturnValue({
            data: mockWatchlists,
            isLoading: false,
            isError: false,
        } as UseQueryResult<Watchlist[], Error>);
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('renders the component title and lists the watchlists', () => {
        render(
            <QueryClientProvider client={queryClient}>
                <WatchlistSelector onSelectWatchlist={() => {}} />
            </QueryClientProvider>
        );
        expect(screen.getByText('My Watchlists')).toBeInTheDocument();
        expect(screen.getByText('Tech Stocks')).toBeInTheDocument();
        expect(screen.getByText('Crypto')).toBeInTheDocument();
    });

    it('calls onSelectWatchlist when a watchlist is clicked', () => {
        const handleSelect = jest.fn();
        render(
            <QueryClientProvider client={queryClient}>
                <WatchlistSelector onSelectWatchlist={handleSelect} />
            </QueryClientProvider>
        );

        fireEvent.click(screen.getByText('Tech Stocks'));
        expect(handleSelect).toHaveBeenCalledWith(mockWatchlists[0]);
    });
});

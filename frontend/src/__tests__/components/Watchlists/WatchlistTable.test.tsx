import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WatchlistTable from '../../../components/Watchlists/WatchlistTable';

const queryClient = new QueryClient();

describe('WatchlistTable', () => {
    it('renders a message when no watchlist is selected', () => {
        render(
            <QueryClientProvider client={queryClient}>
                <WatchlistTable watchlist={null} />
            </QueryClientProvider>
        );
        expect(screen.getByText('Select a watchlist to see the assets.')).toBeInTheDocument();
    });
});

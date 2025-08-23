import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WatchlistsPage from '../../pages/WatchlistsPage';

const queryClient = new QueryClient();

describe('WatchlistsPage', () => {
    it('renders the page title', () => {
        render(
            <QueryClientProvider client={queryClient}>
                <MemoryRouter>
                    <WatchlistsPage />
                </MemoryRouter>
            </QueryClientProvider>
        );
        expect(screen.getByText('Watchlists')).toBeInTheDocument();
    });
});

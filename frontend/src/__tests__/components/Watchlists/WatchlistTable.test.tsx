import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WatchlistTable from '../../../components/Watchlists/WatchlistTable';
import * as useWatchlistsHooks from '../../../hooks/useWatchlists';
import { Watchlist } from '../../../types/watchlist';

jest.mock('../../../hooks/useWatchlists');

const mockUseRemoveWatchlistItem = useWatchlistsHooks.useRemoveWatchlistItem as jest.Mock;

const mockWatchlist: Watchlist = {
  id: 'wl1',
  name: 'My Tech Stocks',
  user_id: 'user1',
  created_at: '2023-01-01T00:00:00Z',
  items: [
    {
      id: 'item1',
      asset_id: 'asset1',
      asset: { id: 'asset1', ticker_symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'STOCK', currency: 'USD', exchange: 'NASDAQ' },
    },
    {
      id: 'item2',
      asset_id: 'asset2',
      asset: { id: 'asset2', ticker_symbol: 'GOOGL', name: 'Alphabet Inc.', asset_type: 'STOCK', currency: 'USD', exchange: 'NASDAQ' },
    },
  ],
};

const queryClient = new QueryClient();

const renderComponent = (props: Partial<React.ComponentProps<typeof WatchlistTable>>) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <WatchlistTable watchlist={mockWatchlist} isLoading={false} error={null} {...props} />
    </QueryClientProvider>
  );
};

describe('WatchlistTable', () => {
  const mockRemoveMutate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRemoveWatchlistItem.mockReturnValue({ mutate: mockRemoveMutate });
  });

  it('renders loading state', () => {
    renderComponent({ isLoading: true, watchlist: undefined });
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    renderComponent({ error: new Error('Failed to load'), watchlist: undefined });
    expect(screen.getByText('Error: Failed to load')).toBeInTheDocument();
  });

  it('renders empty state for a watchlist with no items', () => {
    renderComponent({ watchlist: { ...mockWatchlist, items: [] } });
    expect(screen.getByText('This watchlist is empty.')).toBeInTheDocument();
  });

  it('renders a table with watchlist items', () => {
    renderComponent({});
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();
  });

  it('calls the remove mutation when the remove button is clicked', () => {
    renderComponent({});
    const removeButtons = screen.getAllByRole('button', { name: /Remove/i });
    fireEvent.click(removeButtons[0]);
    expect(mockRemoveMutate).toHaveBeenCalledWith({
      watchlistId: 'wl1',
      itemId: 'item1',
    });
  });

  it('renders price data with correct colors', () => {
    const watchlistWithPrices: Watchlist = {
      ...mockWatchlist,
      items: [
        { ...mockWatchlist.items[0], asset: { ...mockWatchlist.items[0].asset, current_price: 150, day_change: 2.5 } },
        { ...mockWatchlist.items[1], asset: { ...mockWatchlist.items[1].asset, current_price: 2800, day_change: -10 } },
        { id: 'item3', asset_id: 'asset3', asset: { id: 'asset3', ticker_symbol: 'MSFT', name: 'Microsoft', asset_type: 'STOCK', currency: 'USD', exchange: 'NASDAQ', day_change: 0 } },
      ],
    };
    renderComponent({ watchlist: watchlistWithPrices });

    // Check prices are formatted
    expect(screen.getByText('$150.00')).toBeInTheDocument();
    expect(screen.getByText('$2,800.00')).toBeInTheDocument();

    // Check P&L colors
    expect(screen.getByText('$2.50')).toHaveClass('text-green-600');
    expect(screen.getByText('-$10.00')).toHaveClass('text-red-600');
    expect(screen.getByText('$0.00')).toHaveClass('text-gray-900');
  });
});

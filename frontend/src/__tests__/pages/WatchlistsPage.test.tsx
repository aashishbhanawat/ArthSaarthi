import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WatchlistsPage from '../../pages/WatchlistsPage';
import * as useWatchlistsHooks from '../../hooks/useWatchlists';
import { Watchlist } from '../../types/watchlist';

// Mock child components and hooks
jest.mock('../../hooks/useWatchlists');
jest.mock('../../components/Watchlists/WatchlistSelector', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return function DummyWatchlistSelector({ onSelectWatchlist }: { onSelectWatchlist: (id: string) => void }) {
    return React.createElement(
      'div',
      { 'data-testid': 'watchlist-selector-mock' },
      React.createElement('button', { onClick: () => onSelectWatchlist('wl1') }, 'Select Watchlist')
    );
  };
});
jest.mock('../../components/Watchlists/WatchlistTable', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return function DummyWatchlistTable() {
    return React.createElement('div', { 'data-testid': 'watchlist-table-mock' });
  };
});
jest.mock('../../components/modals/AddAssetToWatchlistModal', () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const React = require('react');
    return function DummyAddAssetToWatchlistModal({ isOpen }: { isOpen: boolean }) {
      return isOpen ? React.createElement('div', { 'data-testid': 'add-asset-modal-mock' }) : null;
    };
});

const mockUseWatchlist = useWatchlistsHooks.useWatchlist as jest.Mock;
const mockUseAddWatchlistItem = useWatchlistsHooks.useAddWatchlistItem as jest.Mock;

const mockWatchlist: Watchlist = {
  id: 'wl1',
  name: 'My Tech Stocks',
  user_id: 'user1',
  created_at: '2023-01-01T00:00:00Z',
  items: [],
};

const queryClient = new QueryClient();

const renderComponent = () => {
  return render(
    <QueryClientProvider client={queryClient}>
      <WatchlistsPage />
    </QueryClientProvider>
  );
};

describe('WatchlistsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseWatchlist.mockReturnValue({ data: null, isLoading: false, error: null });
    mockUseAddWatchlistItem.mockReturnValue({ mutate: jest.fn() });
  });

  it('renders placeholder text when no watchlist is selected', () => {
    renderComponent();
    expect(screen.getByText('No watchlist selected')).toBeInTheDocument();
  });

  it('fetches and displays the selected watchlist details', () => {
    mockUseWatchlist.mockReturnValue({ data: mockWatchlist, isLoading: false, error: null });
    renderComponent();

    const selectButton = screen.getByRole('button', { name: 'Select Watchlist' });
    fireEvent.click(selectButton);

    expect(mockUseWatchlist).toHaveBeenCalledWith('wl1');
    expect(screen.getByRole('heading', { name: 'My Tech Stocks' })).toBeInTheDocument();
    expect(screen.getByTestId('watchlist-table-mock')).toBeInTheDocument();
  });

  it('opens the add asset modal when the button is clicked', () => {
    mockUseWatchlist.mockReturnValue({ data: mockWatchlist, isLoading: false, error: null });
    renderComponent();

    // First, select a watchlist to make the button visible
    const selectButton = screen.getByRole('button', { name: 'Select Watchlist' });
    fireEvent.click(selectButton);

    // Then, click the add asset button
    const addAssetButton = screen.getByRole('button', { name: 'Add Asset' });
    fireEvent.click(addAssetButton);

    expect(screen.getByTestId('add-asset-modal-mock')).toBeInTheDocument();
  });
});

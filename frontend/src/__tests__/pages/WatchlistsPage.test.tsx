import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import WatchlistsPage from '../../pages/WatchlistsPage';

// Mock the child component to isolate the page component
jest.mock('../../components/Watchlists/WatchlistSelector', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return function DummyWatchlistSelector({ onSelectWatchlist }: { onSelectWatchlist: (id: string) => void }) {
    return React.createElement(
      'div',
      { 'data-testid': 'watchlist-selector-mock' },
      React.createElement('button', { onClick: () => onSelectWatchlist('1') }, 'Select Watchlist')
    );
  };
});

describe('WatchlistsPage', () => {
  it('renders the WatchlistSelector and placeholder text', () => {
    render(<WatchlistsPage />);

    // Check that the mocked selector is rendered
    expect(screen.getByTestId('watchlist-selector-mock')).toBeInTheDocument();

    // Check for the placeholder text when no watchlist is selected
    expect(screen.getByText('Please select a watchlist to view its items.')).toBeInTheDocument();
  });

  it('updates the displayed text when a watchlist is selected', () => {
    render(<WatchlistsPage />);

    // Simulate selecting a watchlist via the mocked child component
    const selectButton = screen.getByRole('button', { name: 'Select Watchlist' });
    fireEvent.click(selectButton);

    // Check that the text updates to show the selected ID
    expect(screen.getByText('Displaying items for watchlist ID: 1')).toBeInTheDocument();
    expect(screen.queryByText('Please select a watchlist to view its items.')).not.toBeInTheDocument();
  });
});

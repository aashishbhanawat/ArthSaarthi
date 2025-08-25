import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WatchlistSelector from '../../../components/Watchlists/WatchlistSelector';
import * as useWatchlistsHooks from '../../../hooks/useWatchlists';
import { Watchlist } from '../../../types/watchlist';

// Mock the hooks module
jest.mock('../../../hooks/useWatchlists');

const mockUseWatchlists = useWatchlistsHooks.useWatchlists as jest.Mock;
const mockUseCreateWatchlist = useWatchlistsHooks.useCreateWatchlist as jest.Mock;
const mockUseUpdateWatchlist = useWatchlistsHooks.useUpdateWatchlist as jest.Mock;
const mockUseDeleteWatchlist = useWatchlistsHooks.useDeleteWatchlist as jest.Mock;

const mockWatchlists: Watchlist[] = [
  { id: '1', name: 'Tech Giants', user_id: 'user1', created_at: '2023-01-01T00:00:00Z', items: [] },
  { id: '2', name: 'Health Innovators', user_id: 'user1', created_at: '2023-01-02T00:00:00Z', items: [] },
];

const queryClient = new QueryClient();

const renderComponent = (selectedWatchlistId: string | null = null, onSelectWatchlist = jest.fn()) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <WatchlistSelector selectedWatchlistId={selectedWatchlistId} onSelectWatchlist={onSelectWatchlist} />
    </QueryClientProvider>
  );
};

describe('WatchlistSelector', () => {
  const mockCreateMutate = jest.fn();
  const mockUpdateMutate = jest.fn();
  const mockDeleteMutate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseWatchlists.mockReturnValue({ data: mockWatchlists, isLoading: false, error: null });
    mockUseCreateWatchlist.mockReturnValue({ mutate: mockCreateMutate });
    mockUseUpdateWatchlist.mockReturnValue({ mutate: mockUpdateMutate });
    mockUseDeleteWatchlist.mockReturnValue({ mutate: mockDeleteMutate });
    // Mock window.confirm
    window.confirm = jest.fn(() => true);
  });

  it('renders a list of watchlists', () => {
    renderComponent();
    expect(screen.getByText('Tech Giants')).toBeInTheDocument();
    expect(screen.getByText('Health Innovators')).toBeInTheDocument();
  });

  it('calls onSelectWatchlist when a watchlist is clicked', () => {
    const onSelect = jest.fn();
    renderComponent(null, onSelect);
    fireEvent.click(screen.getByText('Tech Giants'));
    expect(onSelect).toHaveBeenCalledWith('1');
  });

  it('opens the form modal in create mode when the add button is clicked', () => {
    renderComponent();
    fireEvent.click(screen.getByRole('button', { name: /add/i }));
    // The modal is a separate component, so we check if its title appears
    expect(screen.getByRole('heading', { name: 'Create New Watchlist' })).toBeInTheDocument();
  });

  it('opens the form modal in edit mode when an edit button is clicked', () => {
    renderComponent();
    const editButtons = screen.getAllByRole('button', { name: /edit/i });
    fireEvent.click(editButtons[0]);
    expect(screen.getByRole('heading', { name: 'Rename Watchlist' })).toBeInTheDocument();
    expect(screen.getByDisplayValue('Tech Giants')).toBeInTheDocument();
  });

  it('calls the delete mutation when a delete button is clicked', () => {
    renderComponent();
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[1]);
    expect(window.confirm).toHaveBeenCalled();
    expect(mockDeleteMutate).toHaveBeenCalledWith('2');
  });

  it('submits the form for creating a watchlist', async () => {
    renderComponent();
    fireEvent.click(screen.getByRole('button', { name: /add/i }));

    const input = screen.getByLabelText('Watchlist Name');
    const saveButton = screen.getByRole('button', { name: 'Save' });

    fireEvent.change(input, { target: { value: 'New Stocks' } });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockCreateMutate).toHaveBeenCalledWith('New Stocks');
    });
  });
});

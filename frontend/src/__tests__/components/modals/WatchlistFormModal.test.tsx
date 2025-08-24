import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WatchlistFormModal from '../../../components/modals/WatchlistFormModal';
import { useCreateWatchlist, useUpdateWatchlist } from '../../../hooks/useWatchlists';
import { Watchlist } from '../../../types/watchlist';

// Mock the custom hooks
jest.mock('../../../hooks/useWatchlists');

const mockUseCreateWatchlist = useCreateWatchlist as jest.Mock;
const mockUseUpdateWatchlist = useUpdateWatchlist as jest.Mock;

const mockWatchlist: Watchlist = { id: '1', name: 'My Watchlist', user_id: '1', created_at: '2023-01-01T00:00:00Z', items: [] };

const queryClient = new QueryClient();

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('WatchlistFormModal', () => {
  const mockCreateMutate = jest.fn();
  const mockUpdateMutate = jest.fn();
  const onClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseCreateWatchlist.mockReturnValue({ mutate: mockCreateMutate });
    mockUseUpdateWatchlist.mockReturnValue({ mutate: mockUpdateMutate });
  });

  it('does not render when isOpen is false', () => {
    renderWithClient(<WatchlistFormModal isOpen={false} onClose={onClose} onSubmit={() => {}} />);
    expect(screen.queryByRole('heading')).not.toBeInTheDocument();
  });

  describe('Create Mode', () => {
    it('renders correctly and calls onSubmit with the new name', async () => {
      const onSubmit = jest.fn();
      renderWithClient(<WatchlistFormModal isOpen={true} onClose={onClose} onSubmit={onSubmit} />);

      expect(screen.getByRole('heading', { name: 'Create New Watchlist' })).toBeInTheDocument();

      const input = screen.getByLabelText('Watchlist Name');
      fireEvent.change(input, { target: { value: 'New Watchlist' } });
      expect(input).toHaveValue('New Watchlist');

      const saveButton = screen.getByRole('button', { name: 'Save' });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith('New Watchlist');
        expect(onClose).toHaveBeenCalled();
      });
    });
  });

  describe('Edit Mode', () => {
    it('renders with pre-filled data and calls onSubmit with the updated name', async () => {
      const onSubmit = jest.fn();
      renderWithClient(<WatchlistFormModal isOpen={true} onClose={onClose} onSubmit={onSubmit} watchlist={mockWatchlist} />);

      expect(screen.getByRole('heading', { name: 'Rename Watchlist' })).toBeInTheDocument();

      const input = screen.getByLabelText('Watchlist Name');
      expect(input).toHaveValue(mockWatchlist.name);

      fireEvent.change(input, { target: { value: 'Updated Name' } });

      const saveButton = screen.getByRole('button', { name: 'Save' });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith('Updated Name');
        expect(onClose).toHaveBeenCalled();
      });
    });
  });

  it('disables save button when name is empty', () => {
    renderWithClient(<WatchlistFormModal isOpen={true} onClose={onClose} onSubmit={() => {}} />);
    const saveButton = screen.getByRole('button', { name: 'Save' });
    expect(saveButton).toBeDisabled();
  });
});

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as watchlistApi from '../../services/watchlistApi';
import {
  useWatchlists,
  useCreateWatchlist,
  useUpdateWatchlist,
  useDeleteWatchlist,
} from '../../hooks/useWatchlists';
import { Watchlist } from '../../types/watchlist';

// Mock the API module
jest.mock('../../services/watchlistApi');

const mockedWatchlistApi = watchlistApi as jest.Mocked<typeof watchlistApi>;

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Turn off retries for testing
      },
    },
  });

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    {children}
  </QueryClientProvider>
);

const mockWatchlists: Watchlist[] = [
  { id: '1', name: 'Tech Stocks', user_id: 'user1', created_at: new Date().toISOString(), items: [] },
  { id: '2', name: 'Healthcare', user_id: 'user1', created_at: new Date().toISOString(), items: [] },
];

describe('Watchlist Hooks', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('useWatchlists', () => {
    it('should return watchlist data on success', async () => {
      mockedWatchlistApi.getWatchlists.mockResolvedValue(mockWatchlists);

      const { result } = renderHook(() => useWatchlists(), { wrapper });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockWatchlists);
    });
  });

  describe('useCreateWatchlist', () => {
    it('should call createWatchlist and invalidate queries on success', async () => {
      const newWatchlist = { ...mockWatchlists[0], id: '3', name: 'New Watchlist' };
      mockedWatchlistApi.createWatchlist.mockResolvedValue(newWatchlist);

      const { result } = renderHook(() => useCreateWatchlist(), { wrapper });

      act(() => {
        result.current.mutate('New Watchlist');
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(mockedWatchlistApi.createWatchlist).toHaveBeenCalledWith('New Watchlist');
    });
  });

  describe('useUpdateWatchlist', () => {
    it('should call updateWatchlist and invalidate queries on success', async () => {
      const updatedWatchlist = { ...mockWatchlists[0], name: 'Updated Name' };
      mockedWatchlistApi.updateWatchlist.mockResolvedValue(updatedWatchlist);

      const { result } = renderHook(() => useUpdateWatchlist(), { wrapper });

      act(() => {
        result.current.mutate({ id: '1', name: 'Updated Name' });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(mockedWatchlistApi.updateWatchlist).toHaveBeenCalledWith('1', 'Updated Name');
    });
  });

  describe('useDeleteWatchlist', () => {
    it('should call deleteWatchlist and invalidate queries on success', async () => {
      mockedWatchlistApi.deleteWatchlist.mockResolvedValue(undefined);

      const { result } = renderHook(() => useDeleteWatchlist(), { wrapper });

      act(() => {
        result.current.mutate('1');
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(mockedWatchlistApi.deleteWatchlist).toHaveBeenCalledWith('1');
    });
  });
});

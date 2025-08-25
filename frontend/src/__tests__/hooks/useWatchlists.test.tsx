import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as watchlistApi from '../../services/watchlistApi';
import {
  useWatchlists,
  useWatchlists,
  useCreateWatchlist,
  useUpdateWatchlist,
  useDeleteWatchlist,
  useWatchlist,
  useWatchlists,
  useCreateWatchlist,
  useUpdateWatchlist,
  useDeleteWatchlist,
  useWatchlist,
  useAddWatchlistItem,
  useRemoveWatchlistItem,
} from '../../hooks/useWatchlists';
import { Watchlist, WatchlistItemCreate } from '../../types/watchlist';
import { Asset } from '../../types/asset';

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

// eslint-disable-next-line @typescript-eslint/ban-types
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>{children}</QueryClientProvider>
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

  describe('useWatchlist', () => {
    it('should return a single watchlist data on success', async () => {
      mockedWatchlistApi.getWatchlist.mockResolvedValue(mockWatchlists[0]);

      const { result } = renderHook(() => useWatchlist('1'), { wrapper });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockWatchlists[0]);
    });
  });

  describe('useAddWatchlistItem', () => {
    it('should call addWatchlistItem and invalidate queries on success', async () => {
      const newItem: WatchlistItemCreate = { asset_id: 'asset3' };
      const mockAsset: Asset = { id: 'asset3', ticker_symbol: 'TSLA', name: 'Tesla Inc.', asset_type: 'STOCK', currency: 'USD', exchange: 'NASDAQ' };
      mockedWatchlistApi.addWatchlistItem.mockResolvedValue({ id: 'item3', ...newItem, asset: mockAsset, watchlist_id: '1', user_id: 'user1' });

      const { result } = renderHook(() => useAddWatchlistItem(), { wrapper });

      act(() => {
        result.current.mutate({ watchlistId: '1', item: newItem });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(mockedWatchlistApi.addWatchlistItem).toHaveBeenCalledWith('1', newItem);
    });
  });

  describe('useRemoveWatchlistItem', () => {
    it('should call removeWatchlistItem and invalidate queries on success', async () => {
      mockedWatchlistApi.removeWatchlistItem.mockResolvedValue(undefined);

      const { result } = renderHook(() => useRemoveWatchlistItem(), { wrapper });

      act(() => {
        result.current.mutate({ watchlistId: '1', itemId: 'item1' });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(mockedWatchlistApi.removeWatchlistItem).toHaveBeenCalledWith('1', 'item1');
    });
  });
});

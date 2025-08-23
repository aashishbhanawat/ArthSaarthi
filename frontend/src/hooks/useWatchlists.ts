import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getWatchlists, createWatchlist, updateWatchlist, deleteWatchlist, addWatchlistItem, deleteWatchlistItem } from '../services/watchlistApi';
import { WatchlistCreate, WatchlistUpdate, WatchlistItemCreate } from '../types/watchlist';

export const useWatchlists = () => {
  const queryClient = useQueryClient();

  const { data: watchlists, isLoading, error } = useQuery({
    queryKey: ['watchlists'],
    queryFn: getWatchlists,
  });

  const createWatchlistMutation = useMutation({
    mutationFn: (newWatchlist: WatchlistCreate) => createWatchlist(newWatchlist),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] });
    },
  });

  const updateWatchlistMutation = useMutation({
    mutationFn: ({ id, updatedWatchlist }: { id: string, updatedWatchlist: WatchlistUpdate }) => updateWatchlist(id, updatedWatchlist),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] });
    },
  });

  const deleteWatchlistMutation = useMutation({
    mutationFn: (id: string) => deleteWatchlist(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] });
    },
  });

  const addWatchlistItemMutation = useMutation({
    mutationFn: ({ watchlistId, item }: { watchlistId: string, item: WatchlistItemCreate }) => addWatchlistItem(watchlistId, item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] });
    },
  });

  const deleteWatchlistItemMutation = useMutation({
    mutationFn: ({ watchlistId, itemId }: { watchlistId: string, itemId: string }) => deleteWatchlistItem(watchlistId, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] });
    },
  });

  return {
    watchlists,
    isLoading,
    error,
    createWatchlist: createWatchlistMutation.mutate,
    updateWatchlist: updateWatchlistMutation.mutate,
    deleteWatchlist: deleteWatchlistMutation.mutate,
    addWatchlistItem: addWatchlistItemMutation.mutate,
    deleteWatchlistItem: deleteWatchlistItemMutation.mutate,
  };
};

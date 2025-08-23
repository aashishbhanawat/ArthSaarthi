import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as watchlistApi from '../services/watchlistApi';

export const useWatchlists = () => {
    return useQuery({
        queryKey: ['watchlists'],
        queryFn: watchlistApi.getWatchlists,
    });
};

export const useCreateWatchlist = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (name: string) => watchlistApi.createWatchlist(name),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['watchlists'] });
        },
    });
};

export const useAddWatchlistItem = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ watchlistId, assetId }: { watchlistId: string; assetId: string }) =>
            watchlistApi.addWatchlistItem(watchlistId, assetId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['watchlists'] });
        },
    });
};

export const useRemoveWatchlistItem = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ watchlistId, itemId }: { watchlistId: string; itemId: string }) =>
            watchlistApi.removeWatchlistItem(watchlistId, itemId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['watchlists'] });
        },
    });
};

export const useUpdateWatchlist = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, name }: { id: string; name: string }) =>
            watchlistApi.updateWatchlist(id, name),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['watchlists'] });
        },
    });
};

export const useDeleteWatchlist = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => watchlistApi.deleteWatchlist(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['watchlists'] });
        },
    });
};

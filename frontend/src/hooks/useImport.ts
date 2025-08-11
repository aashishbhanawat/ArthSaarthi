import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as importApi from '../services/importApi';

export const useCreateImportSession = () => {
    return useMutation({
        mutationFn: ({ portfolioId, file }: { portfolioId: string; file: File }) =>
            importApi.createImportSession(portfolioId, file),
    });
};

export const useImportSession = (sessionId: string) => {
    return useQuery({
        queryKey: ['importSession', sessionId],
        queryFn: () => importApi.getImportSession(sessionId),
        enabled: !!sessionId,
    });
};

export const useParsedTransactions = (sessionId: string) => {
    return useQuery({
        queryKey: ['parsedTransactions', sessionId],
        queryFn: () => importApi.getParsedTransactions(sessionId),
        enabled: !!sessionId,
    });
};

export const useCommitImportSession = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ sessionId }: { sessionId: string; portfolioId: string }) =>
            importApi.commitImportSession(sessionId),
        onSuccess: (_, variables) => {
            const { sessionId, portfolioId } = variables;
            // Invalidate queries to refetch data after commit
            queryClient.invalidateQueries({ queryKey: ['importSession', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['portfolio', portfolioId] });
            queryClient.invalidateQueries({ queryKey: ['transactions', portfolioId] });
            queryClient.invalidateQueries({ queryKey: ['portfolioAnalytics', portfolioId] });
            queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
        },
    });
};
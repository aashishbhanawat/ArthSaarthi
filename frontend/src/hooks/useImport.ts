import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as importApi from '../services/importApi';
import { AssetAliasCreate, ImportSessionCommit } from '../types/import';

export const useCreateImportSession = () => {
    return useMutation({
        mutationFn: ({
            portfolioId,
            source_type,
            file,
        }: {
            portfolioId: string;
            source_type: string;
            file: File;
        }) => importApi.createImportSession(portfolioId, source_type, file),
    });
};

export const useImportSession = (sessionId: string) => {
    return useQuery({
        queryKey: ['importSession', sessionId],
        queryFn: () => importApi.getImportSession(sessionId),
        enabled: !!sessionId,
    });
};

export const useImportSessionPreview = (
    sessionId: string,
    aliasesToCreate: AssetAliasCreate[]
) => {
    return useQuery({
        queryKey: ['importSessionPreview', sessionId, aliasesToCreate],
        queryFn: () => importApi.getImportSessionPreview(sessionId, aliasesToCreate),
        enabled: !!sessionId,
    });
};

export const useCommitImportSession = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            sessionId,
            commitPayload,
        }: {
            sessionId: string;
            commitPayload: ImportSessionCommit;
            portfolioId: string; // Keep for invalidation
        }) => importApi.commitImportSession(sessionId, commitPayload),
        onSuccess: (_, variables) => {
            const { sessionId, portfolioId } = variables;
            // Invalidate queries to refetch data after commit
            queryClient.invalidateQueries({ queryKey: ['importSession', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['importSessionPreview', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['portfolio', portfolioId] });
            queryClient.invalidateQueries({ queryKey: ['transactions', portfolioId] });
            queryClient.invalidateQueries({ queryKey: ['portfolioAnalytics', portfolioId] });
            queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
        },
    });
};
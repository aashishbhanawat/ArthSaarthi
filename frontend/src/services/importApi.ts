import apiClient from './api';
import {
    ImportSession,
    ImportSessionPreview,
    ImportSessionCommit,
} from '../types/import';
import { Msg } from '../types/msg';

export const createImportSession = async (
    portfolioId: string,
    source_type: string,
    file: File
): Promise<ImportSession> => {
    const formData = new FormData();
    formData.append('portfolio_id', portfolioId);
    formData.append('source_type', source_type);
    formData.append('file', file);

    const response = await apiClient.post(
        `/api/v1/import-sessions/`,
        formData,
        {
            headers: { 'Content-Type': 'multipart/form-data' },
        }
    );
    return response.data;
};

export const getImportSession = async (sessionId: string): Promise<ImportSession> => {
    const response = await apiClient.get(`/api/v1/import-sessions/${sessionId}`);
    return response.data;
};

export const getImportSessionPreview = async (
    sessionId: string
): Promise<ImportSessionPreview> => {
    const response = await apiClient.get(`/api/v1/import-sessions/${sessionId}/preview`);
    return response.data;
};

export const commitImportSession = async (
    sessionId: string,
    commitPayload: ImportSessionCommit
): Promise<Msg> => {
    const response = await apiClient.post(
        `/api/v1/import-sessions/${sessionId}/commit`,
        commitPayload
    );
    return response.data;
};
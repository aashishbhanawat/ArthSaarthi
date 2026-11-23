import apiClient from './api';

export interface EdgeModelInfo {
  id: string;
  name: string;
  description: string;
  size_mb: number;
  status: 'NOT_DOWNLOADED' | 'DOWNLOADING' | 'ACTIVE' | 'FAILED';
  progress_percentage: number;
  downloaded_bytes: number;
  total_bytes: number;
  error_message?: string | null;
}

export interface SentimentTestResult {
  label: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  score: number;
  engine: string;
}

export const getEdgeModels = async (): Promise<EdgeModelInfo[]> => {
  const response = await apiClient.get<EdgeModelInfo[]>('/api/v1/ml/models');
  return response.data;
};

export const downloadEdgeModel = async (modelId: string): Promise<EdgeModelInfo> => {
  const response = await apiClient.post<EdgeModelInfo>(`/api/v1/ml/models/${modelId}/download`);
  return response.data;
};

export const getModelProgress = async (modelId: string): Promise<EdgeModelInfo> => {
  const response = await apiClient.get<EdgeModelInfo>(`/api/v1/ml/models/${modelId}/progress`);
  return response.data;
};

export const deleteEdgeModel = async (modelId: string): Promise<{ model_id: string; deleted: boolean }> => {
  const response = await apiClient.delete<{ model_id: string; deleted: boolean }>(`/api/v1/ml/models/${modelId}`);
  return response.data;
};

export const testSentiment = async (text: string): Promise<SentimentTestResult> => {
  const response = await apiClient.post<SentimentTestResult>('/api/v1/ml/sentiment/test', { text });
  return response.data;
};

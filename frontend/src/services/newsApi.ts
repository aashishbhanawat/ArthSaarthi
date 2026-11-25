import apiClient from './api';
import {
  ConcallAnalysis,
  NewsRefreshResponse,
  ResearchFeedResponse,
  ResearchFeedSummary,
} from '../types/marketNews';

export const getResearchFeed = async (params: {
  category?: string;
  symbol?: string;
  sentiment?: string;
  only_holdings?: boolean;
  skip?: number;
  limit?: number;
}): Promise<ResearchFeedResponse> => {
  const response = await apiClient.get<ResearchFeedResponse>('/api/v1/news/feed', {
    params,
  });
  return response.data;
};

export const getResearchSummary = async (
  only_holdings = true
): Promise<ResearchFeedSummary> => {
  const response = await apiClient.get<ResearchFeedSummary>(
    '/api/v1/news/summary',
    { params: { only_holdings } }
  );
  return response.data;
};

export const refreshMarketNews = async (): Promise<NewsRefreshResponse> => {
  const response = await apiClient.post<NewsRefreshResponse>(
    '/api/v1/news/refresh'
  );
  return response.data;
};

export const analyzeConcall = async (
  articleId: string,
  transcriptText?: string,
  checkOnly = false
): Promise<ConcallAnalysis> => {
  const payload: { transcript_text?: string; check_only?: boolean } = {};
  if (transcriptText) payload.transcript_text = transcriptText;
  if (checkOnly) payload.check_only = true;
  const response = await apiClient.post<ConcallAnalysis>(
    `/api/v1/news/${articleId}/analyze-concall`,
    payload,
    { timeout: checkOnly ? 10000 : 300000 } // 10s for status check, 5-minute timeout for edge audio speech-to-text
  );
  return response.data;
};

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
  transcriptText?: string
): Promise<ConcallAnalysis> => {
  const response = await apiClient.post<ConcallAnalysis>(
    `/api/v1/news/${articleId}/analyze-concall`,
    transcriptText ? { transcript_text: transcriptText } : {}
  );
  return response.data;
};

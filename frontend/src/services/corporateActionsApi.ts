import apiClient from './api';
import {
  CorporateActionEventItem,
  CorporateActionEventListResponse,
  CorporateActionTriggerResponse,
} from '../types/corporateActions';

export const getCorporateActionEvents = async (
  status?: string,
  skip = 0,
  limit = 50
): Promise<CorporateActionEventListResponse> => {
  const params: Record<string, unknown> = { skip, limit };
  if (status) {
    params.status = status;
  }
  const response = await apiClient.get<CorporateActionEventListResponse>(
    '/api/v1/corporate-actions/events',
    { params }
  );
  return response.data;
};

export const dismissCorporateActionEvent = async (
  eventId: string
): Promise<CorporateActionEventItem> => {
  const response = await apiClient.post<CorporateActionEventItem>(
    `/api/v1/corporate-actions/events/${encodeURIComponent(eventId)}/dismiss`
  );
  return response.data;
};

export const dismissAllCorporateActionEvents = async (): Promise<{
  message: string;
  dismissed_count: number;
}> => {
  const response = await apiClient.post<{
    message: string;
    dismissed_count: number;
  }>('/api/v1/corporate-actions/events/dismiss-all');
  return response.data;
};

export const adminProcessBondCorporateActions = async (): Promise<CorporateActionTriggerResponse> => {
  const response = await apiClient.post<CorporateActionTriggerResponse>(
    '/api/v1/corporate-actions/admin/process-bonds'
  );
  return response.data;
};

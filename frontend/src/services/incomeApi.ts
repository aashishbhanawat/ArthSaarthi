import apiClient from './api';
import {
  IncomeEntry,
  IncomeEntryPayload,
  IncomeFYSummary,
  IncomeSource,
  IncomeSourcePayload,
} from '../types/income';

// Income Sources APIs
export const getIncomeSources = async (): Promise<IncomeSource[]> => {
  const response = await apiClient.get<IncomeSource[]>('/api/v1/income/sources');
  return response.data;
};

export const createIncomeSource = async (
  payload: IncomeSourcePayload
): Promise<IncomeSource> => {
  const response = await apiClient.post<IncomeSource>(
    '/api/v1/income/sources',
    payload
  );
  return response.data;
};

export const updateIncomeSource = async (
  id: string,
  payload: Partial<IncomeSourcePayload>
): Promise<IncomeSource> => {
  const response = await apiClient.put<IncomeSource>(
    `/api/v1/income/sources/${id}`,
    payload
  );
  return response.data;
};

export const deleteIncomeSource = async (id: string): Promise<IncomeSource> => {
  const response = await apiClient.delete<IncomeSource>(
    `/api/v1/income/sources/${id}`
  );
  return response.data;
};

// Income Entries APIs
export const getIncomeEntries = async (
  financialYear?: string,
  sourceId?: string
): Promise<IncomeEntry[]> => {
  const params: Record<string, string> = {};
  if (financialYear) params.financial_year = financialYear;
  if (sourceId) params.source_id = sourceId;

  const response = await apiClient.get<IncomeEntry[]>('/api/v1/income/entries', {
    params,
  });
  return response.data;
};

export const createIncomeEntry = async (
  payload: IncomeEntryPayload
): Promise<IncomeEntry> => {
  const response = await apiClient.post<IncomeEntry>(
    '/api/v1/income/entries',
    payload
  );
  return response.data;
};

export const updateIncomeEntry = async (
  id: string,
  payload: Partial<IncomeEntryPayload>
): Promise<IncomeEntry> => {
  const response = await apiClient.put<IncomeEntry>(
    `/api/v1/income/entries/${id}`,
    payload
  );
  return response.data;
};

export const deleteIncomeEntry = async (id: string): Promise<IncomeEntry> => {
  const response = await apiClient.delete<IncomeEntry>(
    `/api/v1/income/entries/${id}`
  );
  return response.data;
};

export const getIncomeFYSummary = async (
  financialYear: string
): Promise<IncomeFYSummary> => {
  const response = await apiClient.get<IncomeFYSummary>('/api/v1/income/summary', {
    params: { financial_year: financialYear },
  });
  return response.data;
};

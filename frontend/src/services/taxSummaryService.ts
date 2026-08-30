import apiClient from './api';
import { TaxSummaryResponse } from '../types/tax_summary';

export const getTaxSummary = async (
  financialYear: string = '2024-25'
): Promise<TaxSummaryResponse> => {
  const response = await apiClient.get<TaxSummaryResponse>('/api/v1/tax/summary', {
    params: { financial_year: financialYear },
  });
  return response.data;
};

export const getExportCsvUrl = (financialYear: string): string => {
  const baseURL = apiClient.defaults.baseURL || '';
  return `${baseURL}/api/v1/tax/summary/export/csv?financial_year=${financialYear}`;
};

export const getExportPdfUrl = (financialYear: string): string => {
  const baseURL = apiClient.defaults.baseURL || '';
  return `${baseURL}/api/v1/tax/summary/export/pdf?financial_year=${financialYear}`;
};

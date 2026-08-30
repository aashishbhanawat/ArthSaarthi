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

export const downloadExportCsv = async (financialYear: string): Promise<void> => {
  const response = await apiClient.get('/api/v1/tax/summary/export/csv', {
    params: { financial_year: financialYear },
    responseType: 'blob',
  });
  const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `tax_summary_${financialYear}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const downloadExportPdf = async (financialYear: string): Promise<void> => {
  const response = await apiClient.get('/api/v1/tax/summary/export/pdf', {
    params: { financial_year: financialYear },
    responseType: 'blob',
  });
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `tax_summary_${financialYear}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

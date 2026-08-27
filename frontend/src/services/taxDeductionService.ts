import apiClient from './api';
import {
  TaxDeduction,
  TaxDeductionCreate,
  TaxDeductionFYSummary,
  TaxDeductionUpdate,
} from '../types/tax_deduction';

export const getTaxDeductions = async (
  financialYear?: string,
  section?: string
): Promise<TaxDeduction[]> => {
  const params: Record<string, string> = {};
  if (financialYear) params.financial_year = financialYear;
  if (section) params.section = section;

  const response = await apiClient.get<TaxDeduction[]>('/api/v1/tax/deductions', {
    params,
  });
  return response.data;
};

export const createTaxDeduction = async (
  payload: TaxDeductionCreate
): Promise<TaxDeduction> => {
  const response = await apiClient.post<TaxDeduction>(
    '/api/v1/tax/deductions',
    payload
  );
  return response.data;
};

export const updateTaxDeduction = async (
  id: string,
  payload: TaxDeductionUpdate
): Promise<TaxDeduction> => {
  const response = await apiClient.put<TaxDeduction>(
    `/api/v1/tax/deductions/${id}`,
    payload
  );
  return response.data;
};

export const deleteTaxDeduction = async (id: string): Promise<TaxDeduction> => {
  const response = await apiClient.delete<TaxDeduction>(
    `/api/v1/tax/deductions/${id}`
  );
  return response.data;
};

export const getTaxDeductionsSummary = async (
  financialYear: string
): Promise<TaxDeductionFYSummary> => {
  const response = await apiClient.get<TaxDeductionFYSummary>(
    '/api/v1/tax/deductions/summary',
    {
      params: { financial_year: financialYear },
    }
  );
  return response.data;
};

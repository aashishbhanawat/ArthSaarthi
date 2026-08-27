import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as incomeApi from '../services/incomeApi';
import { IncomeEntryPayload, IncomeSourcePayload } from '../types/income';

export const useIncomeSources = () => {
  return useQuery({
    queryKey: ['incomeSources'],
    queryFn: () => incomeApi.getIncomeSources(),
  });
};

export const useIncomeEntries = (financialYear?: string, sourceId?: string) => {
  return useQuery({
    queryKey: ['incomeEntries', financialYear, sourceId],
    queryFn: () => incomeApi.getIncomeEntries(financialYear, sourceId),
  });
};

export const useIncomeSummary = (financialYear: string) => {
  return useQuery({
    queryKey: ['incomeSummary', financialYear],
    queryFn: () => incomeApi.getIncomeFYSummary(financialYear),
    enabled: !!financialYear,
  });
};

export const useCreateIncomeSource = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: IncomeSourcePayload) => incomeApi.createIncomeSource(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomeSources'] });
    },
  });
};

export const useUpdateIncomeSource = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<IncomeSourcePayload> }) =>
      incomeApi.updateIncomeSource(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomeSources'] });
      queryClient.invalidateQueries({ queryKey: ['incomeEntries'] });
      queryClient.invalidateQueries({ queryKey: ['incomeSummary'] });
    },
  });
};

export const useDeleteIncomeSource = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => incomeApi.deleteIncomeSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomeSources'] });
      queryClient.invalidateQueries({ queryKey: ['incomeEntries'] });
      queryClient.invalidateQueries({ queryKey: ['incomeSummary'] });
    },
  });
};

export const useCreateIncomeEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: IncomeEntryPayload) => incomeApi.createIncomeEntry(payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['incomeEntries'] });
      queryClient.invalidateQueries({ queryKey: ['incomeSummary', variables.financial_year] });
    },
  });
};

export const useUpdateIncomeEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<IncomeEntryPayload> }) =>
      incomeApi.updateIncomeEntry(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomeEntries'] });
      queryClient.invalidateQueries({ queryKey: ['incomeSummary'] });
    },
  });
};

export const useDeleteIncomeEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => incomeApi.deleteIncomeEntry(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomeEntries'] });
      queryClient.invalidateQueries({ queryKey: ['incomeSummary'] });
    },
  });
};

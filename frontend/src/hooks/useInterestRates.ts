import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as adminApi from '../services/adminApi';
import { HistoricalInterestRateCreate, HistoricalInterestRateUpdate } from '../types/interestRate';

export const useInterestRates = () => {
  return useQuery({
    queryKey: ['interestRates'],
    queryFn: adminApi.getInterestRates,
  });
};

export const useCreateInterestRate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rateData: HistoricalInterestRateCreate) => adminApi.createInterestRate(rateData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interestRates'] });
    },
  });
};

export const useUpdateInterestRate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ rateId, rateData }: { rateId: string; rateData: HistoricalInterestRateUpdate }) =>
      adminApi.updateInterestRate(rateId, rateData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interestRates'] });
    },
  });
};

export const useDeleteInterestRate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rateId: string) => adminApi.deleteInterestRate(rateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interestRates'] });
    },
  });
};
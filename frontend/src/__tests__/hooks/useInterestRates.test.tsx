import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as adminApi from '../../services/adminApi';
import {
  useInterestRates,
  useCreateInterestRate,
  useUpdateInterestRate,
  useDeleteInterestRate,
} from '../../hooks/useInterestRates';
import { HistoricalInterestRate } from '../../types/interestRate';
import React from 'react';

// Mock the adminApi service
jest.mock('../../services/adminApi');
const mockedAdminApi = adminApi as jest.Mocked<typeof adminApi>;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockRates: HistoricalInterestRate[] = [
  { id: '1', scheme_name: 'PPF', rate: 7.1, start_date: '2023-04-01', end_date: '2024-03-31' },
];

describe('useInterestRates hooks', () => {
  afterEach(() => {
    jest.clearAllMocks();
    queryClient.clear();
  });

  it('should fetch interest rates successfully using useInterestRates', async () => {
    mockedAdminApi.getInterestRates.mockResolvedValue(mockRates);
    const { result } = renderHook(() => useInterestRates(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockRates);
  });

  it('should create an interest rate and invalidate queries on success', async () => {
    const newRate = { scheme_name: 'NSC', rate: 7.7, start_date: '2024-04-01', end_date: '2025-03-31' };
    mockedAdminApi.createInterestRate.mockResolvedValue({ ...newRate, id: '2' });
    const invalidateQueriesSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useCreateInterestRate(), { wrapper });
    result.current.mutate(newRate);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedAdminApi.createInterestRate).toHaveBeenCalledWith(newRate);
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['interestRates'] });
  });

  it('should update an interest rate and invalidate queries on success', async () => {
    const rateToUpdate = { rateId: '1', rateData: { scheme_name: 'PPF', rate: 7.2, start_date: '2023-04-01', end_date: '2024-03-31' } };
    mockedAdminApi.updateInterestRate.mockResolvedValue({ ...rateToUpdate.rateData, id: '1' });
    const invalidateQueriesSpy = jest.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useUpdateInterestRate(), { wrapper });
    result.current.mutate(rateToUpdate);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedAdminApi.updateInterestRate).toHaveBeenCalledWith(rateToUpdate.rateId, rateToUpdate.rateData);
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['interestRates'] });
  });

  it('should delete an interest rate and invalidate queries on success', async () => {
    const rateIdToDelete = '1';
    mockedAdminApi.deleteInterestRate.mockResolvedValue(mockRates[0]);
    const invalidateQueriesSpy = jest.spyOn(queryClient, 'invalidateQueries');
    const { result } = renderHook(() => useDeleteInterestRate(), { wrapper });
    result.current.mutate(rateIdToDelete);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedAdminApi.deleteInterestRate).toHaveBeenCalledWith(rateIdToDelete);
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['interestRates'] });
  });
});
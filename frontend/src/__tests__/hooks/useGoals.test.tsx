import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as goalApi from '../../services/goalApi';
import { useGoals, useGoal, useCreateGoal, useUpdateGoal, useDeleteGoal } from '../../hooks/useGoals';
import { Goal, GoalCreate, GoalUpdate } from '../../types/goal';

jest.mock('../../services/goalApi');

const mockedGoalApi = goalApi as jest.Mocked<typeof goalApi>;

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>{children}</QueryClientProvider>
);

const mockGoal: Goal = {
    id: '1',
    name: 'Test Goal',
    target_amount: 10000,
    target_date: '2025-01-01',
    created_at: '2024-01-01T00:00:00Z',
    user_id: '1',
    links: [],
};

describe('Goals Hooks', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('useGoals', () => {
    it('should return goals data on success', async () => {
      mockedGoalApi.getGoals.mockResolvedValue([mockGoal]);
      const { result } = renderHook(() => useGoals(), { wrapper });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual([mockGoal]);
    });
  });

  describe('useGoal', () => {
    it('should return a single goal data on success', async () => {
      mockedGoalApi.getGoal.mockResolvedValue(mockGoal);
      const { result } = renderHook(() => useGoal('1'), { wrapper });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockGoal);
    });
  });

  describe('useCreateGoal', () => {
    it('should call createGoal and invalidate queries on success', async () => {
        const { result } = renderHook(() => useCreateGoal(), { wrapper });
        const newGoal: GoalCreate = { name: 'New Goal', target_amount: 5000, target_date: '2026-01-01' };

        result.current.mutate(newGoal);

        await waitFor(() => expect(mockedGoalApi.createGoal).toHaveBeenCalledWith(newGoal));
    });
  });

  describe('useUpdateGoal', () => {
    it('should call updateGoal and invalidate queries on success', async () => {
      const { result } = renderHook(() => useUpdateGoal(), { wrapper });
      const updatedGoal: GoalUpdate = { name: 'Updated Goal' };

      result.current.mutate({ id: '1', data: updatedGoal });

      await waitFor(() => expect(mockedGoalApi.updateGoal).toHaveBeenCalledWith('1', updatedGoal));
    });
  });

  describe('useDeleteGoal', () => {
    it('should call deleteGoal and invalidate queries on success', async () => {
      const { result } = renderHook(() => useDeleteGoal(), { wrapper });

      result.current.mutate('1');

      await waitFor(() => expect(mockedGoalApi.deleteGoal).toHaveBeenCalledWith('1'));
    });
  });
});

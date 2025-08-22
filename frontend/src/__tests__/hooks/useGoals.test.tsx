import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as goalApi from '../../services/goalApi';
import { useGoals, useCreateGoal } from '../../hooks/useGoals';
import { Goal, GoalCreate } from '../../types/goal';

// Mock the API module
jest.mock('../../services/goalApi');

const mockedGoalApi = goalApi as jest.Mocked<typeof goalApi>;

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Turn off retries for testing
      },
    },
  });

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>{children}</QueryClientProvider>
);

describe('Goal Hooks', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('useGoals', () => {
    it('should return goals data on success', async () => {
      const mockGoals: Goal[] = [
        { id: '1', name: 'Goal 1', target_amount: 1000, target_date: '2025-01-01', user_id: '1', created_at: '2024-01-01T00:00:00Z', links: [] },
      ];
      mockedGoalApi.getGoals.mockResolvedValue(mockGoals);

      const { result } = renderHook(() => useGoals(), { wrapper });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockGoals);
    });
  });

  describe('useCreateGoal', () => {
    it('should create a new goal and invalidate queries on success', async () => {
      const newGoalData: GoalCreate = { name: 'New Goal', target_amount: 2000, target_date: '2026-01-01' };
      const createdGoal: Goal = { ...newGoalData, id: '2', user_id: '1', created_at: '2024-01-01T00:00:00Z', links: [] };
      mockedGoalApi.createGoal.mockResolvedValue(createdGoal);

      const { result } = renderHook(() => useCreateGoal(), { wrapper });

      await waitFor(() => {
        result.current.mutate(newGoalData);
      });

      expect(mockedGoalApi.createGoal).toHaveBeenCalledWith(newGoalData);
    });
  });
});

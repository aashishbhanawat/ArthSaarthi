import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as goalApi from '../../services/goalApi';
import {
  useGoals,
  useCreateGoal,
  useUpdateGoal,
  useDeleteGoal,
} from '../../hooks/useGoals';
import { Goal, GoalCreate, GoalUpdate } from '../../types/goal';

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

// eslint-disable-next-line @typescript-eslint/ban-types
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>{children}</QueryClientProvider>
);

const mockGoals: Goal[] = [
  { id: '1', name: 'Buy a car', target_amount: 25000, target_date: '2025-12-31', user_id: 'user1' },
  { id: '2', name: 'House Downpayment', target_amount: 100000, target_date: '2027-01-01', user_id: 'user1' },
];

describe('Goal Hooks', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('useGoals', () => {
    it('should return goal data on success', async () => {
      mockedGoalApi.getGoals.mockResolvedValue(mockGoals);

      const { result } = renderHook(() => useGoals(), { wrapper });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockGoals);
    });
  });

  describe('useCreateGoal', () => {
    it('should call createGoal and invalidate queries on success', async () => {
      const newGoal: GoalCreate = { name: 'New Goal', target_amount: 5000, target_date: '2024-12-31' };
      const createdGoal: Goal = { ...newGoal, id: '3', user_id: 'user1' };
      mockedGoalApi.createGoal.mockResolvedValue(createdGoal);

      const { result } = renderHook(() => useCreateGoal(), { wrapper });

      act(() => {
        result.current.mutate(newGoal);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(mockedGoalApi.createGoal).toHaveBeenCalledWith(newGoal);
    });
  });

  describe('useUpdateGoal', () => {
    it('should call updateGoal and invalidate queries on success', async () => {
      const updatedGoalData: GoalUpdate = { name: 'Updated Name' };
      const updatedGoal: Goal = { ...mockGoals[0], ...updatedGoalData };
      mockedGoalApi.updateGoal.mockResolvedValue(updatedGoal);

      const { result } = renderHook(() => useUpdateGoal(), { wrapper });

      act(() => {
        result.current.mutate({ id: '1', goal: updatedGoalData });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(mockedGoalApi.updateGoal).toHaveBeenCalledWith('1', updatedGoalData);
    });
  });

  describe('useDeleteGoal', () => {
    it('should call deleteGoal and invalidate queries on success', async () => {
        mockedGoalApi.deleteGoal.mockResolvedValue({ msg: "Goal deleted successfully" });

      const { result } = renderHook(() => useDeleteGoal(), { wrapper });

      act(() => {
        result.current.mutate('1');
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(mockedGoalApi.deleteGoal).toHaveBeenCalledWith('1');
    });
  });
});

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GoalDetailView from '../../../components/Goals/GoalDetailView';
import * as goalApi from '../../../services/goalApi';
import { Goal, GoalProgress } from '../../../types/goal';

jest.mock('../../../services/goalApi');

const mockedGoalApi = goalApi as jest.Mocked<typeof goalApi>;

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('GoalDetailView', () => {
  it('should render goal progress', async () => {
    const mockGoal: Goal = {
      id: '1',
      name: 'Test Goal',
      target_amount: 1000,
      target_date: '2025-01-01',
      user_id: '1',
      created_at: '2024-01-01T00:00:00Z',
      links: [],
    };
    const mockProgress: GoalProgress = {
      goal_id: '1',
      current_value: 500,
      target_amount: 1000,
      progress_percentage: 50,
    };
    mockedGoalApi.getGoalProgress.mockResolvedValue(mockProgress);

    render(<GoalDetailView goal={mockGoal} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/50.00% Complete/)).toBeInTheDocument();
    });
  });
});

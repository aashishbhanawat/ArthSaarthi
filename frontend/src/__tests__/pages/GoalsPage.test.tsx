import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GoalsPage from '../../pages/GoalsPage';
import { useGoals } from '../../hooks/useGoals';
import { Goal } from '../../types/goal';

jest.mock('../../hooks/useGoals');

const mockedUseGoals = useGoals as jest.Mock;

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('GoalsPage', () => {
  it('should render loading state', () => {
    mockedUseGoals.mockReturnValue({ isLoading: true });
    render(<GoalsPage />, { wrapper });
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should render error state', () => {
    mockedUseGoals.mockReturnValue({ error: new Error('An error occurred') });
    render(<GoalsPage />, { wrapper });
    expect(screen.getByText(/An error occurred/)).toBeInTheDocument();
  });

  it('should render goals data', () => {
    const mockGoals: Goal[] = [
      { id: '1', name: 'Goal 1', target_amount: 1000, target_date: '2025-01-01', user_id: '1', created_at: '2024-01-01T00:00:00Z', links: [] },
    ];
    mockedUseGoals.mockReturnValue({ data: mockGoals, isLoading: false, error: null });
    render(<GoalsPage />, { wrapper });
    expect(screen.getByText('Goal 1')).toBeInTheDocument();
  });
});

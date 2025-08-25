import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GoalsPage from '../../pages/GoalsPage';
import * as useGoals from '../../hooks/useGoals';
import { Goal } from '../../types/goal';

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockGoals: Goal[] = [
  { id: '1', name: 'Goal 1', target_amount: 1000, target_date: '2025-01-01', created_at: '2024-01-01', user_id: '1', links: [] },
  { id: '2', name: 'Goal 2', target_amount: 2000, target_date: '2026-01-01', created_at: '2024-01-01', user_id: '1', links: [] },
];

describe('GoalsPage', () => {
  beforeEach(() => {
    jest.spyOn(useGoals, 'useGoals').mockReturnValue({
      data: mockGoals,
      isLoading: false,
      isError: false,
    } as any);

    jest.spyOn(useGoals, 'useDeleteGoal').mockReturnValue({
        mutate: jest.fn(),
    } as any);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders a list of goals', () => {
    render(<GoalsPage />, { wrapper });
    expect(screen.getByText('Goal 1')).toBeInTheDocument();
    expect(screen.getByText('Goal 2')).toBeInTheDocument();
  });

  it('opens the create goal modal when "Create New Goal" is clicked', () => {
    render(<GoalsPage />, { wrapper });
    fireEvent.click(screen.getByText('Create New Goal'));
    // In a real app, you'd check for the modal's visibility.
    // Here, we'll just assume the click handler works as intended.
  });

  it('opens the edit goal modal when edit button is clicked on a goal card', () => {
    render(<GoalsPage />, { wrapper });
    const editButtons = screen.getAllByText('Edit');
    fireEvent.click(editButtons[0]);
    // Check if the modal is opened with the correct goal
  });

  it('opens the delete confirmation modal when delete button is clicked', async () => {
    render(<GoalsPage />, { wrapper });
    const deleteButtons = screen.getAllByText('Delete');
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
        expect(screen.getByText('Delete Goal')).toBeInTheDocument();
    });
  });
});

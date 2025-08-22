import React from 'react';
import { render, screen } from '@testing-library/react';
import GoalCard from '../../../components/Goals/GoalCard';
import { Goal } from '../../../types/goal';

describe('GoalCard', () => {
  it('should render goal name', () => {
    const mockGoal: Goal = {
      id: '1',
      name: 'Test Goal',
      target_amount: 1000,
      target_date: '2025-01-01',
      user_id: '1',
      created_at: '2024-01-01T00:00:00Z',
      links: [],
    };
    render(<GoalCard goal={mockGoal} />);
    expect(screen.getByText('Test Goal')).toBeInTheDocument();
  });
});

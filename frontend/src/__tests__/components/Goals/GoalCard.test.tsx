import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import GoalCard from '../../../components/Goals/GoalCard';
import { Goal } from '../../../types/goal';

const mockGoal: Goal = {
  id: '1',
  name: 'Buy a Tesla',
  target_amount: 50000,
  target_date: '2026-12-31T00:00:00Z',
  created_at: '2024-01-01T00:00:00Z',
  user_id: '1',
  links: [],
};

const renderWithRouter = (ui: React.ReactElement) => {
    return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe('GoalCard', () => {
  it('renders goal information correctly', () => {
    renderWithRouter(<GoalCard goal={mockGoal} onEdit={() => {}} onDelete={() => {}} />);

    expect(screen.getByText('Buy a Tesla')).toBeInTheDocument();
    expect(screen.getByText(/Target: ₹50,000.00 by 31 Dec 2026/i)).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    const handleEdit = jest.fn();
    renderWithRouter(<GoalCard goal={mockGoal} onEdit={handleEdit} onDelete={() => {}} />);

    fireEvent.click(screen.getByText('Edit'));
    expect(handleEdit).toHaveBeenCalledWith(mockGoal);
  });

  it('calls onDelete when delete button is clicked', () => {
    const handleDelete = jest.fn();
    renderWithRouter(<GoalCard goal={mockGoal} onEdit={() => {}} onDelete={handleDelete} />);

    fireEvent.click(screen.getByText('Delete'));
    expect(handleDelete).toHaveBeenCalledWith(mockGoal);
  });
});

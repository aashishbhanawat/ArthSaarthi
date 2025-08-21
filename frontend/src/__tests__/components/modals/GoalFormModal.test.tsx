import React from 'react';
import { render, screen } from '@testing-library/react';
import GoalFormModal from '../../../components/modals/GoalFormModal';

describe('GoalFormModal', () => {
  it('should render when open', () => {
    render(<GoalFormModal isOpen={true} onClose={() => {}} />);
    expect(screen.getByText('Create Goal')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    render(<GoalFormModal isOpen={false} onClose={() => {}} />);
    expect(screen.queryByText('Create Goal')).not.toBeInTheDocument();
  });
});

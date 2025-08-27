import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GoalFormModal from '../../../components/modals/GoalFormModal';
import { Goal } from '../../../types/goal';

const queryClient = new QueryClient();

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

const mockGoal: Goal = { id: '1', name: 'Buy a car', target_amount: 25000, target_date: '2025-12-31', user_id: 'user1' };

describe('GoalFormModal', () => {
  const onClose = jest.fn();
  const onSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not render when isOpen is false', () => {
    renderWithClient(<GoalFormModal isOpen={false} onClose={onClose} onSubmit={onSubmit} />);
    expect(screen.queryByRole('heading')).not.toBeInTheDocument();
  });

  describe('Create Mode', () => {
    it('renders correctly and calls onSubmit with the new goal data', async () => {
      renderWithClient(<GoalFormModal isOpen={true} onClose={onClose} onSubmit={onSubmit} />);

      expect(screen.getByRole('heading', { name: 'Create New Goal' })).toBeInTheDocument();

      fireEvent.change(screen.getByLabelText('Goal Name'), { target: { value: 'New Goal' } });
      fireEvent.change(screen.getByLabelText('Target Amount'), { target: { value: '50000' } });
      fireEvent.change(screen.getByLabelText('Target Date'), { target: { value: '2026-01-01' } });

      fireEvent.click(screen.getByRole('button', { name: 'Create Goal' }));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          name: 'New Goal',
          target_amount: 50000,
          target_date: '2026-01-01',
        });
      });
      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Edit Mode', () => {
    it('renders with pre-filled data and calls onSubmit with the updated goal data', async () => {
      renderWithClient(<GoalFormModal isOpen={true} onClose={onClose} onSubmit={onSubmit} goal={mockGoal} />);

      expect(screen.getByRole('heading', { name: 'Edit Goal' })).toBeInTheDocument();

      expect(screen.getByLabelText('Goal Name')).toHaveValue(mockGoal.name);
      expect(screen.getByLabelText('Target Amount')).toHaveValue(mockGoal.target_amount);
      expect(screen.getByLabelText('Target Date')).toHaveValue(mockGoal.target_date);

      fireEvent.change(screen.getByLabelText('Goal Name'), { target: { value: 'Updated Goal Name' } });

      fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          name: 'Updated Goal Name',
          target_amount: mockGoal.target_amount,
          target_date: mockGoal.target_date,
        });
      });
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('disables save button when form is incomplete', () => {
    renderWithClient(<GoalFormModal isOpen={true} onClose={onClose} onSubmit={onSubmit} />);
    expect(screen.getByRole('button', { name: 'Create Goal' })).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Goal Name'), { target: { value: 'Test' } });
    expect(screen.getByRole('button', { name: 'Create Goal' })).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Target Amount'), { target: { value: '1000' } });
    expect(screen.getByRole('button', { name: 'Create Goal' })).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Target Date'), { target: { value: '2025-01-01' } });
    expect(screen.getByRole('button', { name: 'Create Goal' })).not.toBeDisabled();
  });
});

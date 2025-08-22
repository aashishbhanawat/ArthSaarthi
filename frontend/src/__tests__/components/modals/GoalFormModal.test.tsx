import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GoalFormModal from '../../../components/modals/GoalFormModal';

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('GoalFormModal', () => {
  it('should render when open', () => {
    render(<GoalFormModal isOpen={true} onClose={() => {}} />, { wrapper });
    expect(screen.getByRole('heading', { name: /create goal/i })).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    render(<GoalFormModal isOpen={false} onClose={() => {}} />, { wrapper });
    expect(screen.queryByRole('heading', { name: /create goal/i })).not.toBeInTheDocument();
  });
});

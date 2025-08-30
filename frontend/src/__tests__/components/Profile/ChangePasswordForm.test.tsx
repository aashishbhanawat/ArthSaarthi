import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useChangePassword } from '../../../hooks/useProfile';
import ChangePasswordForm from '../../../components/Profile/ChangePasswordForm';

// Mock the hook
jest.mock('../../../hooks/useProfile');

const mockUseChangePassword = useChangePassword as jest.Mock;
const queryClient = new QueryClient();

const AllTheProviders = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('ChangePasswordForm', () => {
  const mockMutate = jest.fn();

  beforeEach(() => {
    mockUseChangePassword.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
    });
    jest.clearAllMocks();
  });

  it('renders correctly', () => {
    render(<ChangePasswordForm />, { wrapper: AllTheProviders });
    expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^new password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument();
  });

  it('shows validation error if passwords do not match', async () => {
    render(<ChangePasswordForm />, { wrapper: AllTheProviders });
    fireEvent.change(screen.getByLabelText(/^new password$/i), { target: { value: 'NewValidPassword123!' } });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'DoesNotMatch!' } });
    fireEvent.click(screen.getByRole('button', { name: /update password/i }));

    expect(await screen.findByText('Passwords do not match')).toBeInTheDocument();
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it('shows validation error for invalid new password', async () => {
    render(<ChangePasswordForm />, { wrapper: AllTheProviders });
    fireEvent.change(screen.getByLabelText(/^new password$/i), { target: { value: 'weak' } });
    fireEvent.click(screen.getByRole('button', { name: /update password/i }));

    expect(await screen.findByText(/Password must be at least 8 characters long/i)).toBeInTheDocument();
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it('submits the form with valid data', async () => {
    render(<ChangePasswordForm />, { wrapper: AllTheProviders });
    fireEvent.change(screen.getByLabelText(/current password/i), { target: { value: 'OldValidPassword123!' } });
    fireEvent.change(screen.getByLabelText(/^new password$/i), { target: { value: 'NewValidPassword123!' } });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'NewValidPassword123!' } });
    fireEvent.click(screen.getByRole('button', { name: /update password/i }));

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith(
        {
          old_password: 'OldValidPassword123!',
          new_password: 'NewValidPassword123!',
        },
        expect.any(Object)
      );
    });
  });

  it('disables the button while submitting', () => {
    mockUseChangePassword.mockReturnValue({
      mutate: mockMutate,
      isPending: true,
    });
    render(<ChangePasswordForm />, { wrapper: AllTheProviders });
    expect(screen.getByRole('button', { name: /updating/i })).toBeDisabled();
  });
});

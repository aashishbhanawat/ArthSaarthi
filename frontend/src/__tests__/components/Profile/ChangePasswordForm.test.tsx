import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ChangePasswordForm from '../../../components/Profile/ChangePasswordForm';
import * as useProfile from '../../../hooks/useProfile';

const queryClient = new QueryClient();

const mockChangePassword = jest.fn();

const renderComponent = () => {
  return render(
    <QueryClientProvider client={queryClient}>
      <ChangePasswordForm />
    </QueryClientProvider>
  );
};

describe('ChangePasswordForm', () => {
  beforeEach(() => {
    jest.spyOn(useProfile, 'useChangePassword').mockReturnValue({
      mutate: mockChangePassword,
      isPending: false,
      isSuccess: false,
      error: null,
      reset: jest.fn(),
    });
    mockChangePassword.mockClear();
  });

  it('allows a user to change their password', async () => {
    mockChangePassword.mockImplementation((_variables, options) => {
      options.onSuccess();
    });

    renderComponent();

    const oldPasswordInput = screen.getByLabelText(/current password/i);
    const newPasswordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText(/confirm new password/i);
    const updateButton = screen.getByRole('button', { name: /update password/i });

    fireEvent.change(oldPasswordInput, { target: { value: 'oldPass123!' } });
    fireEvent.change(newPasswordInput, { target: { value: 'newPass123!' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'newPass123!' } });

    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(mockChangePassword).toHaveBeenCalledWith(
        { old_password: 'oldPass123!', new_password: 'newPass123!' },
        expect.any(Object)
      );
    });
  });

  it('shows an error if new passwords do not match', async () => {
    renderComponent();

    const newPasswordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText(/confirm new password/i);
    const updateButton = screen.getByRole('button', { name: /update password/i });

    fireEvent.change(newPasswordInput, { target: { value: 'newPass123!' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'differentPass123!' } });
    fireEvent.click(updateButton);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/new passwords do not match/i);
    expect(mockChangePassword).not.toHaveBeenCalled();
  });
});

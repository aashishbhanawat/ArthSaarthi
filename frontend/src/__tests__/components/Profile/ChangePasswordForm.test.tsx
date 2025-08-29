import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ChangePasswordForm from '../../../components/Profile/ChangePasswordForm';
import * as useUsers from '../../../hooks/useUsers';

const queryClient = new QueryClient();

const mockUseUpdatePassword = jest.spyOn(useUsers, 'useUpdatePassword');

const renderWithProviders = (ui: React.ReactElement) => {
    return render(
        <QueryClientProvider client={queryClient}>
            {ui}
        </QueryClientProvider>
    );
};

describe('ChangePasswordForm', () => {
    it('submits correct data and shows success message', async () => {
        const mutate = jest.fn();
        mockUseUpdatePassword.mockReturnValue({ mutate, isPending: false, isSuccess: true, error: null, reset: jest.fn() });

        renderWithProviders(<ChangePasswordForm />);

        fireEvent.change(screen.getByLabelText(/current password/i), { target: { value: 'oldPassword123' } });
        fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'newPassword123' } });
        fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'newPassword123' } });

        fireEvent.click(screen.getByRole('button', { name: /change password/i }));

        await waitFor(() => {
            expect(mutate).toHaveBeenCalledWith(
                { old_password: 'oldPassword123', new_password: 'newPassword123' },
                expect.any(Object)
            );
        });
    });

    it('shows an error if new passwords do not match', async () => {
        const reset = jest.fn();
        mockUseUpdatePassword.mockReturnValue({ mutate: jest.fn(), isPending: false, isSuccess: false, error: null, reset });
        renderWithProviders(<ChangePasswordForm />);

        fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'newPassword123' } });
        fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'differentPassword' } });

        fireEvent.click(screen.getByRole('button', { name: /change password/i }));

        await waitFor(() => {
            expect(screen.getByText(/new passwords do not match/i)).toBeInTheDocument();
        });
    });

    it('shows an api error message on failure', async () => {
        const mutate = jest.fn();
        mockUseUpdatePassword.mockReturnValue({ mutate, isPending: false, isSuccess: false, error: { response: { data: { detail: 'Incorrect old password' } } }, reset: jest.fn() });

        renderWithProviders(<ChangePasswordForm />);

        fireEvent.click(screen.getByRole('button', { name: /change password/i }));

        expect(await screen.findByText(/incorrect old password/i)).toBeInTheDocument();
    });
});

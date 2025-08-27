import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthContext } from '../../../context/AuthContext';
import UpdateProfileForm from '../../../components/Profile/UpdateProfileForm';
import * as useUsers from '../../../hooks/useUsers';

const queryClient = new QueryClient();

const mockUseUpdateMe = jest.spyOn(useUsers, 'useUpdateMe');

const renderWithProviders = (ui: React.ReactElement, authValue: any) => {
    return render(
        <QueryClientProvider client={queryClient}>
            <AuthContext.Provider value={authValue}>
                {ui}
            </AuthContext.Provider>
        </QueryClientProvider>
    );
};

describe('UpdateProfileForm', () => {
    it('renders with initial user data and allows updating', async () => {
        const mutate = jest.fn();
        mockUseUpdateMe.mockReturnValue({ mutate, isPending: false });

        const authContextValue = {
            user: { full_name: 'Initial Name', email: 'test@example.com' },
            setUser: jest.fn(),
        };

        renderWithProviders(<UpdateProfileForm />, authContextValue);

        const nameInput = screen.getByLabelText(/full name/i);
        expect(nameInput).toHaveValue('Initial Name');

        fireEvent.change(nameInput, { target: { value: 'Updated Name' } });
        expect(nameInput).toHaveValue('Updated Name');

        fireEvent.click(screen.getByRole('button', { name: /save/i }));

        await waitFor(() => {
            expect(mutate).toHaveBeenCalledWith({ full_name: 'Updated Name' });
        });
    });

    it('shows a loading state when submitting', () => {
        mockUseUpdateMe.mockReturnValue({ mutate: jest.fn(), isPending: true });

        const authContextValue = {
            user: { full_name: 'Initial Name', email: 'test@example.com' },
            setUser: jest.fn(),
        };

        renderWithProviders(<UpdateProfileForm />, authContextValue);
        expect(screen.getByRole('button', { name: /saving.../i })).toBeDisabled();
    });
});

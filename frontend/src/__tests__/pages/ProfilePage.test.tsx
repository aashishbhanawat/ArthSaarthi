import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthContext } from '../../context/AuthContext';
import ProfilePage from '../../pages/ProfilePage';

const queryClient = new QueryClient();


const renderWithProviders = (ui: React.ReactElement, authValue: any) => {
    return render(
        <QueryClientProvider client={queryClient}>
            <AuthContext.Provider value={authValue}>
                <MemoryRouter>
                    {ui}
                </MemoryRouter>
            </AuthContext.Provider>
        </QueryClientProvider>
    );
};

describe('ProfilePage', () => {
    it('renders the heading and both form components', () => {
        const authContextValue = {
            user: { full_name: 'Test User', email: 'test@example.com' },
            setUser: jest.fn(),
        };

        renderWithProviders(<ProfilePage />, authContextValue);

        expect(screen.getByRole('heading', { name: /profile settings/i })).toBeInTheDocument();
    });
});

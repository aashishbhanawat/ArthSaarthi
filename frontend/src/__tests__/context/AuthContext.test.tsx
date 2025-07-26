import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from '../../context/AuthContext';
import * as api from '../../services/api';

// Mock the API service
jest.mock('../../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
}));

// Mock localStorage
const localStorageMock = (() => {
    let store: { [key: string]: string } = {};
    return {
        getItem: (key: string) => store[key] || null,
        setItem: (key: string, value: string) => {
            store[key] = value.toString();
        },
        removeItem: (key: string) => {
            delete store[key];
        },
        clear: () => {
            store = {};
        },
    };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

const TestComponent = () => {
    const { user, loading } = useAuth();
    if (loading) return <div>Loading...</div>;
    return <div>{user ? `User: ${user.email}` : 'No User'}</div>;
};

const renderComponent = (initialRoute = '/') => {
    return render(
        <MemoryRouter initialEntries={[initialRoute]}>
            <AuthProvider>
                <Routes>
                    <Route path="/" element={<TestComponent />} />
                    <Route path="/login" element={<div>Login Page</div>} />
                </Routes>
            </AuthProvider>
        </MemoryRouter>
    );
};

describe('AuthContext', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorageMock.clear();
    });

    it('initializes with no user if no token is in localStorage', async () => {
        renderComponent();
        expect(await screen.findByText('No User')).toBeInTheDocument();
    });

    it('fetches user data if a token exists in localStorage', async () => {
        localStorageMock.setItem('token', 'fake-token');
        mockedApi.getCurrentUser.mockResolvedValue({ id: 1, email: 'test@test.com', full_name: 'Test User', is_admin: false, is_active: true });

        renderComponent();

        expect(await screen.findByText('User: test@test.com')).toBeInTheDocument();
        expect(mockedApi.getCurrentUser).toHaveBeenCalledTimes(1);
    });

    it('handles successful token refresh', async () => {
        // 1. Start with an expired token
        localStorageMock.setItem('token', 'expired-token');
        
        // 2. First API call fails with 401
        mockedApi.getCurrentUser.mockRejectedValueOnce({ response: { status: 401 } });
        
        // 3. Refresh token call succeeds
        mockedApi.refreshToken.mockResolvedValueOnce({ access_token: 'new-valid-token' });
        
        // 4. Second API call (the retry) succeeds
        mockedApi.getCurrentUser.mockResolvedValueOnce({ id: 1, email: 'refreshed@test.com', full_name: 'Refreshed User', is_admin: false, is_active: true });

        renderComponent();

        await waitFor(() => {
            expect(screen.getByText('User: refreshed@test.com')).toBeInTheDocument();
        });

        expect(mockedApi.refreshToken).toHaveBeenCalledTimes(1);
        expect(localStorageMock.getItem('token')).toBe('new-valid-token');
        expect(mockedApi.getCurrentUser).toHaveBeenCalledTimes(2);
    });

    it('logs out the user on failed token refresh', async () => {
        // 1. Start with an expired token
        localStorageMock.setItem('token', 'expired-token');
        
        // 2. First API call fails with 401
        mockedApi.getCurrentUser.mockRejectedValueOnce({ response: { status: 401 } });
        
        // 3. Refresh token call also fails
        mockedApi.refreshToken.mockRejectedValueOnce(new Error('Invalid refresh token'));
        
        mockedApi.logoutUser.mockResolvedValue();

        renderComponent();

        await waitFor(() => {
            expect(screen.getByText('Login Page')).toBeInTheDocument();
        });

        expect(mockedApi.refreshToken).toHaveBeenCalledTimes(1);
        expect(mockedApi.logoutUser).toHaveBeenCalledTimes(1);
        expect(localStorageMock.getItem('token')).toBeNull();
        expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
    });

    it('does not attempt to refresh token for non-401 errors', async () => {
        localStorageMock.setItem('token', 'valid-token');
        mockedApi.getCurrentUser.mockRejectedValueOnce({ response: { status: 500 } });

        renderComponent();

        await waitFor(() => expect(screen.getByText('No User')).toBeInTheDocument());
        expect(mockedApi.refreshToken).not.toHaveBeenCalled();
    });
});
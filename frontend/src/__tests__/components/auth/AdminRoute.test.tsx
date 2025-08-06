import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import '@testing-library/jest-dom';
import AdminRoute from '../../../components/auth/AdminRoute';
import { useAuth } from '../../../context/AuthContext';

// Mock the useAuth hook
jest.mock('../../../context/AuthContext');



describe('AdminRoute', () => {
    const mockUseAuth = useAuth as jest.Mock;

    it('renders child routes for admin users', () => {
        mockUseAuth.mockReturnValue({ user: { is_admin: true } });
        render(
            <MemoryRouter initialEntries={['/admin/dashboard']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
                <Routes>
                    <Route element={<AdminRoute />}>
                        <Route path="/admin/dashboard" element={<div>Admin Page</div>} />
                    </Route>
                </Routes>
            </MemoryRouter>
        );
        expect(screen.getByText('Admin Page')).toBeInTheDocument();
    });

    it('redirects non-admin users to the dashboard', () => {
        mockUseAuth.mockReturnValue({ user: { is_admin: false } });
        render(
            <MemoryRouter initialEntries={['/admin/dashboard']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
                <Routes>
                    <Route element={<AdminRoute />}>
                        <Route path="/admin/dashboard" element={<div>Admin Page</div>} />
                    </Route>
                    <Route path="/dashboard" element={<div>User Dashboard</div>} />
                </Routes>
            </MemoryRouter>
        );
        expect(screen.getByText('User Dashboard')).toBeInTheDocument();
        expect(screen.queryByText('Admin Page')).not.toBeInTheDocument();
    });

    it('renders nothing while user data is loading', () => {
        mockUseAuth.mockReturnValue({ user: null });
        const { container } = render( // eslint-disable-line testing-library/render-result-naming-convention
            <MemoryRouter initialEntries={['/admin/dashboard']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
                <Routes>
                    <Route element={<AdminRoute />}>
                        <Route path="/admin/dashboard" element={<div>Admin Page</div>} />
                    </Route>
                </Routes>
            </MemoryRouter>
        );
        expect(container).toBeEmptyDOMElement();
    });
});
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import '@testing-library/jest-dom';
import AdminRoute from '../../../components/auth/AdminRoute';
import { useAuth } from '../../../context/AuthContext';

// Mock the useAuth hook
jest.mock('../../../context/AuthContext');

const renderWithRouter = (ui: React.ReactNode, initialRoute = '/') => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path="/" element={ui} />
        <Route path="/admin" element={<AdminRoute />}>
          <Route index element={<div>Admin Content</div>} />
        </Route>
        <Route path="/unauthorized" element={<div>Unauthorized</div>} />
      </Routes>
    </MemoryRouter>
  );
};

describe('AdminRoute', () => {
  test('renders children for admin users', () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: { is_admin: true },
      isLoading: false,
    });

    renderWithRouter(<div>Home</div>, '/admin');
    expect(screen.getByText('Admin Content')).toBeInTheDocument();
  });

  test('navigates to home for non-admin users', () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: { is_admin: false },
      isLoading: false,
    });

    renderWithRouter(<div>Home</div>, '/admin');
    expect(screen.getByText('Home')).toBeInTheDocument(); // We are redirected to the home page which renders 'Home'
  });

  test('renders loading state', () => {
    (useAuth as jest.Mock).mockReturnValue({ user: null, isLoading: true });
    renderWithRouter(<div>Home</div>, '/admin');
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});
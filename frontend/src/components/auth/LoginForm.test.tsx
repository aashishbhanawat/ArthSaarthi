import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from '../../context/AuthContext'; // This was missing
import LoginForm from './LoginForm';
import * as api from '../../services/api';

jest.mock('../../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

const mockLogin = jest.fn();

const renderWithContext = () => {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={{ login: mockLogin, logout: jest.fn(), token: null, user: null, loading: false }}>
        <LoginForm />
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('LoginForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the login form correctly', () => {
    renderWithContext();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('allows the user to enter email and password', () => {
    renderWithContext();
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(emailInput).toHaveValue('test@example.com');
    expect(passwordInput).toHaveValue('password123');
  });

  it('calls login api and calls context login function on successful submission', async () => {
    mockedApi.loginUser.mockResolvedValue({ access_token: 'fake-token', token_type: 'bearer' });

    renderWithContext();

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockedApi.loginUser).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(mockLogin).toHaveBeenCalledWith('fake-token');
    });
  });

  it('shows an error message on failed submission', async () => {
    const errorMessage = 'Invalid credentials';
    mockedApi.loginUser.mockRejectedValue({ response: { data: { detail: errorMessage } } });

    renderWithContext();

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrongpassword' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });
});
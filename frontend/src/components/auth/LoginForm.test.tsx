import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from  '../../context/AuthContext';
import LoginForm from './LoginForm';
import * as api from '../../services/api';


// Mock dependencies
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

jest.mock('../../services/api');
const mockedApi = api as jest.Mocked<typeof api>; 

const mockLogin = jest.fn();

// A wrapper component that provides the AuthContext
const renderWithContext = () => {
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthContext.Provider value={{ login: mockLogin, logout: jest.fn(), token: null, user: null, isLoading: false, error: null, register: jest.fn() }}>
        <LoginForm />
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('LoginForm', () => {
  beforeEach(() => {
    // Clear mock history before each test
    mockLogin.mockClear();
    mockedApi.loginUser.mockClear();
  });

  it('renders the login form correctly', () => {
    renderWithContext();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('allows the user to enter email and password', async () => {
    renderWithContext();
    const user = userEvent.setup();

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    expect(emailInput).toHaveValue('test@example.com');
    expect(passwordInput).toHaveValue('password123');
  });

  it('calls login api and calls context login function on successful submission', async () => {
    mockedApi.loginUser.mockResolvedValue({ access_token: 'fake-token' });
    renderWithContext();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('fake-token');
    });
    expect(mockedApi.loginUser).toHaveBeenCalledWith('test@example.com', 'password123');
  });

  it('shows an error message on failed submission', async () => {
    const errorMessage = 'Incorrect email or password';
    mockedApi.loginUser.mockRejectedValue({ response: { data: { detail: errorMessage } } });
    renderWithContext();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/email/i), 'wrong@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

});
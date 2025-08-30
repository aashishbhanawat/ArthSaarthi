import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthContext } from '../../../context/AuthContext';
import { useUpdateProfile } from '../../../hooks/useProfile';
import UpdateProfileForm from '../../../components/Profile/UpdateProfileForm';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the hooks
jest.mock('../../../hooks/useProfile');

const mockUseUpdateProfile = useUpdateProfile as jest.Mock;

const queryClient = new QueryClient();

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const authContextValue = {
    user: { email: 'test@example.com', full_name: 'Test User', id: '1', is_active: true, is_admin: false },
    setUser: jest.fn(),
    logout: jest.fn(),
    loading: false,
    deploymentMode: 'server',
  };

  return (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authContextValue}>
        {children}
      </AuthContext.Provider>
    </QueryClientProvider>
  );
};


describe('UpdateProfileForm', () => {
  const mockMutate = jest.fn();

  beforeEach(() => {
    mockUseUpdateProfile.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
    });
    jest.clearAllMocks();
  });

  it('renders the form with the current user data', () => {
    render(<UpdateProfileForm />, { wrapper: AllTheProviders });
    expect(screen.getByLabelText(/full name/i)).toHaveValue('Test User');
    expect(screen.getByLabelText(/email/i)).toHaveValue('test@example.com');
  });

  it('enables save button only when form is dirty', () => {
    render(<UpdateProfileForm />, { wrapper: AllTheProviders });
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    expect(saveButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Updated Name' } });
    expect(saveButton).not.toBeDisabled();
  });

  it('submits the form with the updated full name', async () => {
    render(<UpdateProfileForm />, { wrapper: AllTheProviders });
    const fullNameInput = screen.getByLabelText(/full name/i);
    const saveButton = screen.getByRole('button', { name: /save changes/i });

    fireEvent.change(fullNameInput, { target: { value: 'Updated Name' } });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith({ full_name: 'Updated Name' });
    });
  });

  it('disables the button while submitting', () => {
    mockUseUpdateProfile.mockReturnValue({
      mutate: mockMutate,
      isPending: true,
    });
    render(<UpdateProfileForm />, { wrapper: AllTheProviders });
    fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Updated Name' } });
    expect(screen.getByRole('button', { name: /saving/i })).toBeDisabled();
  });
});

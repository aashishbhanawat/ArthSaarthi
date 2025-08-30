import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthContext } from '../../../context/AuthContext';
import UpdateProfileForm from '../../../components/Profile/UpdateProfileForm';
import * as useProfile from '../../../hooks/useProfile';

const queryClient = new QueryClient();

const mockUser = {
  id: '1',
  email: 'test@example.com',
  full_name: 'Test User',
  is_active: true,
  is_admin: false,
};

const mockSetUser = jest.fn();

const renderComponent = () => {
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={{
        user: mockUser,
        login: jest.fn(),
        logout: jest.fn(),
        setUser: mockSetUser,
        deploymentMode: 'server'
      }}>
        <UpdateProfileForm />
      </AuthContext.Provider>
    </QueryClientProvider>
  );
};

describe('UpdateProfileForm', () => {
  it('renders the form with user data and allows updating the profile', async () => {
    const mockUpdateProfile = jest.fn();
    jest.spyOn(useProfile, 'useUpdateProfile').mockReturnValue({
      mutate: mockUpdateProfile,
      isPending: false,
    });

    renderComponent();

    const nameInput = screen.getByLabelText(/full name/i);
    expect(nameInput).toHaveValue(mockUser.full_name);

    const newName = 'Updated Test User';
    fireEvent.change(nameInput, { target: { value: newName } });
    expect(nameInput).toHaveValue(newName);

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith({ full_name: newName });
    });
  });
});

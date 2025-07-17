import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import UserFormModal from '../../../components/Admin/UserFormModal';
import { useCreateUser, useUpdateUser } from '../../../hooks/useUsers';
import { User } from '../../../types/user';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the custom hooks
jest.mock('../../../hooks/useUsers');

const mockUseCreateUser = useCreateUser as jest.Mock;
const mockUseUpdateUser = useUpdateUser as jest.Mock;

const mockUser: User = { id: 1, email: 'test@example.com', full_name: 'Test User', is_active: true, is_admin: false };

const queryClient = new QueryClient();

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('UserFormModal', () => {
  const mockMutateAsync = jest.fn().mockResolvedValue({});
  const onClose = jest.fn();

  beforeEach(() => {
    mockMutateAsync.mockClear();
    onClose.mockClear();
    mockUseCreateUser.mockReturnValue({ mutateAsync: mockMutateAsync, isPending: false });
    mockUseUpdateUser.mockReturnValue({ mutateAsync: mockMutateAsync, isPending: false });
  });

  describe('Create Mode', () => {
    test('renders correctly and submits new user data', async () => {
      renderWithClient(<UserFormModal isOpen={true} onClose={onClose} userToEdit={null} />);

      expect(screen.getByRole('heading', { name: 'Create New User' })).toBeInTheDocument();
      
      // Fill out the form
      fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'New User' } });
      fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'new@example.com' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Password123!' } });
      
      // Submit the form
      fireEvent.click(screen.getByRole('button', { name: 'Create User' }));

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
            full_name: 'New User',
          email: 'new@example.com',
          password: 'Password123!',
        });
      });

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled();
      });

    });
    test("displays error messages from API on failed user creation", async () => {
      const mockError = {
        response: {
          data: {
            detail: [{ loc: ["body", "email"], msg: "Email already exists" }],
          },
        },
      };
      mockUseCreateUser.mockReturnValue({
        mutateAsync: jest.fn().mockRejectedValue(mockError),
        isPending: false,
      });
  
      renderWithClient(<UserFormModal isOpen={true} onClose={onClose} userToEdit={null} />);
      fireEvent.change(screen.getByLabelText("Full Name"), { target: { value: "Existing User" } });
      fireEvent.change(screen.getByLabelText("Email"), { target: { value: "existing@example.com" } });
      fireEvent.change(screen.getByLabelText("Password"), { target: { value: "ValidPassword123!" } });
      fireEvent.click(screen.getByRole("button", { name: "Create User" }));
  
      await waitFor(() => {
        expect(screen.getByText("Email already exists")).toBeInTheDocument();
      });
    });
  });

  describe('Edit Mode', () => {
    test('renders with pre-filled user data', () => {
      renderWithClient(<UserFormModal isOpen={true} onClose={onClose} userToEdit={mockUser} />);
      expect(screen.getByRole('heading', { name: 'Edit User' })).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
      // Password field should not be present in edit mode
      expect(screen.queryByLabelText('Password')).not.toBeInTheDocument();
    });

    test('submits updated user data', async () => {
      renderWithClient(<UserFormModal isOpen={true} onClose={onClose} userToEdit={mockUser} />);
      // Change some data
      fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'Updated Name' } });
      fireEvent.click(screen.getByLabelText('Administrator')); // Make the user an admin

      // Submit the form
      fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          userId: mockUser.id,
          userData: {
            full_name: 'Updated Name',
            email: 'test@example.com',
            is_active: true,
            is_admin: true,
          },
        });
      });

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled();
      });

    });

    test("displays error messages from API on failed user update", async () => {
        const mockError = {
          response: {
            data: {
              detail: [{ loc: ["body", "full_name"], msg: "Full name cannot be empty" }],
            },
          },
        };
        mockUseUpdateUser.mockReturnValue({
          mutateAsync: jest.fn().mockRejectedValue(mockError),
          isPending: false,
        });
    
        renderWithClient(<UserFormModal isOpen={true} onClose={onClose} userToEdit={mockUser} />);
        fireEvent.change(screen.getByLabelText("Full Name"), { target: { value: "" } });
        fireEvent.click(screen.getByRole("button", { name: "Save Changes" }));
    
        await waitFor(() => {
          expect(screen.getByText("Full name cannot be empty")).toBeInTheDocument();
        });
    });
  });
});
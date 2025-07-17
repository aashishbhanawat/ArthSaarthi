import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import UserManagementPage from '../../../pages/Admin/UserManagementPage';
import { useUsers, useDeleteUser, useCreateUser, useUpdateUser } from '../../../hooks/useUsers';
import { User } from '../../../types/user';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the custom hooks
jest.mock('../../../hooks/useUsers');

const mockUseDeleteUser = useDeleteUser as jest.Mock;
const mockUseUsers = useUsers as jest.Mock;
const mockUseCreateUser = useCreateUser as jest.Mock;
const mockUseUpdateUser = useUpdateUser as jest.Mock;
const mockUsers: User[] = [
  { id: 1, email: 'admin@example.com', full_name: 'Admin User', is_active: true, is_admin: true },
  { id: 2, email: 'test@example.com', full_name: 'Test User', is_active: true, is_admin: false },
];

const queryClient = new QueryClient();

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('UserManagementPage', () => {
  beforeEach(() => {
    // Reset mocks before each test
    mockUseUsers.mockClear();
    mockUseDeleteUser.mockReturnValue({ mutate: jest.fn() });
  });

  test('renders loading state correctly', () => {
    mockUseUsers.mockReturnValue({ data: [], isLoading: true, error: null });
    renderWithClient(<UserManagementPage />);
    expect(screen.getByText('Loading users...')).toBeInTheDocument();
  });

  test('renders error state correctly', () => {
    const errorMessage = 'Failed to fetch users';
    mockUseUsers.mockReturnValue({ data: [], isLoading: false, error: new Error(errorMessage) });
    renderWithClient(<UserManagementPage />);
    expect(screen.getByText(`An error occurred: ${errorMessage}`)).toBeInTheDocument();
  });

  test('renders users table with data', () => {
    mockUseUsers.mockReturnValue({ data: mockUsers, isLoading: false, error: null });
    renderWithClient(<UserManagementPage />);
    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('Admin User')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  test('opens create user modal when "Create New User" is clicked', async () => {
    mockUseUsers.mockReturnValue({ data: mockUsers, isLoading: false, error: null });
    mockUseCreateUser.mockReturnValue({
      mutateAsync: jest.fn(),
    });
    mockUseUpdateUser.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    });
    renderWithClient(<UserManagementPage />);

    fireEvent.click(screen.getByText('Create New User'));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Create New User' })).toBeInTheDocument();
    });
  });

  test('opens edit user modal when "Edit" is clicked', async () => {
    mockUseUsers.mockReturnValue({ data: mockUsers, isLoading: false, error: null });
        mockUseUpdateUser.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    });
    renderWithClient(<UserManagementPage />);

    // Get all Edit buttons and click the first one
    const editButtons = screen.getAllByRole('button', { name: 'Edit' });
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Edit User' })).toBeInTheDocument();
      // Check if the form is pre-filled
      expect(screen.getByDisplayValue('Admin User')).toBeInTheDocument();
    });
  });

  test('opens delete confirmation modal when "Delete" is clicked', async () => {
    mockUseUsers.mockReturnValue({ data: mockUsers, isLoading: false, error: null });
    renderWithClient(<UserManagementPage />);

    const deleteButtons = screen.getAllByRole('button', { name: 'Delete' });
    fireEvent.click(deleteButtons[1]); // Click delete for the non-admin user

    await waitFor(() => {
      const modal = screen.getByRole('heading', { name: 'Confirm Deletion' }).closest('.modal-content');
      expect(modal).toBeInTheDocument();
      expect(
        within(modal!).getByText(/are you sure you want to delete the user/i)
      ).toBeInTheDocument();
      expect(within(modal!).getByText('Test User')).toBeInTheDocument();
    });
  });
});
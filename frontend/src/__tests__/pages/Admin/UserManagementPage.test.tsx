import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import UserManagementPage from '../../../pages/Admin/UserManagementPage';
import { useUsers, useDeleteUser, useCreateUser, useUpdateUser } from '../../../hooks/useUsers';
import { User } from '../../../types/user';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock child components to isolate the page component for unit testing
jest.mock('../../../components/Admin/UsersTable', () => {
  const React = require('react');
  return (props: any) =>
    React.createElement('div', { 'data-testid': 'users-table' },
      React.createElement('button', { onClick: () => props.onEdit(mockUsers[0]) }, 'Edit'),
      React.createElement('button', { onClick: () => props.onDelete(mockUsers[1]) }, 'Delete')
    );
});
jest.mock('../../../components/Admin/UserFormModal', () => {
  const React = require('react');
  return ({ userToEdit, onClose }: any) =>
    React.createElement('div', { 'data-testid': 'user-form-modal' },
      React.createElement('h2', null, userToEdit ? 'Edit User' : 'Create New User'),
      React.createElement('button', { onClick: onClose }, 'Close')
    );
});
jest.mock('../../../components/Admin/DeleteConfirmationModal', () => {
  const React = require('react');
  return ({ user, onClose, onConfirm }: any) =>
    React.createElement('div', { 'data-testid': 'delete-confirmation-modal' },
      React.createElement('h2', null, 'Delete User'),
      React.createElement('p', null, user?.email),
      React.createElement('button', { onClick: onConfirm }, 'Confirm Delete'),
      React.createElement('button', { onClick: onClose }, 'Cancel')
    );
});

// Mock the custom data hooks
jest.mock('../../../hooks/useUsers');

const mockUsers: User[] = [
  { id: 'user-1', email: 'admin@example.com', full_name: 'Admin User', is_active: true, is_admin: true, portfolios: [] },
  { id: 'user-2', email: 'test@example.com', full_name: 'Test User', is_active: true, is_admin: false, portfolios: [] },
];

const queryClient = new QueryClient();

const mockUseUsers = useUsers as jest.Mock;
const mockUseDeleteUser = useDeleteUser as jest.Mock;
const mockUseCreateUser = useCreateUser as jest.Mock;
const mockUseUpdateUser = useUpdateUser as jest.Mock;

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('UserManagementPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset mocks before each test
    mockUseDeleteUser.mockReturnValue({ mutate: jest.fn() });
    mockUseCreateUser.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({}),
      isPending: false,
    });
    mockUseUpdateUser.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({}),
      isPending: false,
    });
  });

  test('renders loading state correctly', () => {
    mockUseUsers.mockReturnValue({ data: [], isLoading: true, error: null });
    renderWithClient(<UserManagementPage />);
    expect(screen.getByText('Loading users...')).toBeInTheDocument();
  });

  test('renders error state correctly', () => {
    const errorMessage = 'Failed to fetch users';
    mockUseUsers.mockReturnValue({ data: [], isLoading: false, isError: true, error: new Error(errorMessage) });
    renderWithClient(<UserManagementPage />);
    expect(screen.getByText(`Error: ${errorMessage}`)).toBeInTheDocument();
  });

  test('renders users table with data', () => {
    mockUseUsers.mockReturnValue({ data: mockUsers, isLoading: false, error: null });
    renderWithClient(<UserManagementPage />);
    // The UsersTable is now mocked, so we check for its test ID
    expect(screen.getByTestId('users-table')).toBeInTheDocument();
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

    fireEvent.click(screen.getByRole('button', { name: 'Create New User' }));

    await waitFor(() => {
      // Check that our mocked modal is rendered
      expect(screen.getByTestId('user-form-modal')).toBeInTheDocument();
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
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));

    await waitFor(() => {
      expect(screen.getByTestId('user-form-modal')).toBeInTheDocument();
      // Check that the mocked modal shows the correct title for edit mode
      expect(screen.getByText('Edit User')).toBeInTheDocument();
    });
  });

  test('opens delete confirmation modal when "Delete" is clicked', async () => {
    mockUseUsers.mockReturnValue({ data: mockUsers, isLoading: false, error: null });
    renderWithClient(<UserManagementPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => {
      expect(screen.getByTestId('delete-confirmation-modal')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });
  });
});
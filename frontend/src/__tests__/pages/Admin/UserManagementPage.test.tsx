import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import UserManagementPage from '../../../pages/Admin/UserManagementPage';
import { useUsers, useDeleteUser, useCreateUser, useUpdateUser } from '../../../hooks/useUsers';
import { User } from '../../../types/user';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock child components to isolate the page component for unit testing
interface MockUsersTableProps {
  users: User[];
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
}
jest.mock('../../../components/Admin/UsersTable', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return (props: MockUsersTableProps) =>
    React.createElement('div', { 'data-testid': 'users-table' },
      React.createElement('button', { onClick: () => props.onEdit(mockUsers[0]) }, 'Edit'),
      React.createElement('button', { onClick: () => props.onDelete(mockUsers[1]) }, 'Delete')
    );
});

interface MockUserFormModalProps {
  userToEdit: User | null;
  onClose: () => void;
}
jest.mock('../../../components/Admin/UserFormModal', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return ({ userToEdit, onClose }: MockUserFormModalProps) =>
    React.createElement('div', { 'data-testid': 'user-form-modal' },
      React.createElement('h2', null, userToEdit ? 'Edit User' : 'Create New User'),
      React.createElement('button', { onClick: onClose }, 'Close')
    );
});

interface MockDeleteConfirmationModalProps {
  title: string;
  message: React.ReactNode;
  onClose: () => void;
  onConfirm: () => void;
}
jest.mock('../../../components/common/DeleteConfirmationModal', () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const React = require('react');
    // The component is a NAMED export, so the mock must return an object
    // with a property matching the component's name.
    const MockedModal = ({ title, message, onClose, onConfirm }: MockDeleteConfirmationModalProps) =>
        React.createElement('div', { 'data-testid': 'delete-confirmation-modal' },
            React.createElement('h2', null, title),
            React.createElement('div', null, message),
            React.createElement('button', { onClick: onConfirm }, 'Confirm Delete'),
            React.createElement('button', { onClick: onClose }, 'Cancel')
        );
    return { DeleteConfirmationModal: MockedModal };
});

// Mock the custom data hooks
jest.mock('../../../hooks/useUsers');

const mockUsers: User[] = [
    { id: '1', email: 'admin@example.com', full_name: 'Admin User', is_active: true, is_admin: true },
    { id: '2', email: 'test@example.com', full_name: 'Test User', is_active: true, is_admin: false },
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

        const modal = await screen.findByTestId('user-form-modal');
        expect(modal).toBeInTheDocument();
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

        const modalTitle = await screen.findByText('Edit User');
        expect(modalTitle).toBeInTheDocument();
        expect(screen.getByTestId('user-form-modal')).toBeInTheDocument();
    });

    test('opens delete confirmation modal when "Delete" is clicked', async () => {
        mockUseUsers.mockReturnValue({ data: mockUsers, isLoading: false, error: null });
        renderWithClient(<UserManagementPage />);

        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

        const userEmail = await screen.findByText('test@example.com');
        expect(userEmail).toBeInTheDocument();
        expect(screen.getByTestId('delete-confirmation-modal')).toBeInTheDocument();
    });
});
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import UsersTable from '../../../components/Admin/UsersTable';
import { User } from '../../../types/user';

const mockUsers: User[] = [
  { id: '1', email: 'admin@example.com', full_name: 'Admin User', is_active: true, is_admin: true },
  { id: '2', email: 'test@example.com', full_name: 'Test User', is_active: false, is_admin: false },
];

describe('UsersTable', () => {
  const onEdit = jest.fn();
  const onDelete = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = () => {
    render(<UsersTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);
  };

  test('renders table headers and user data correctly', () => {
    renderComponent();
    expect(screen.getAllByText('admin@example.com').length).toBeGreaterThan(0);
    expect(screen.getAllByText('test@example.com').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Admin').length).toBeGreaterThan(0);
    expect(screen.getAllByText('User').length).toBeGreaterThan(0);
  });

  test('calls onEdit with the correct user when Edit button is clicked', () => {
    renderComponent();
    const editButton = screen.getByRole('button', { name: `Edit user ${mockUsers[1].email}` });
    fireEvent.click(editButton); // Click edit for the second user
    expect(onEdit).toHaveBeenCalledWith(mockUsers[1]);
  });

  test('calls onDelete with the correct user when Delete button is clicked', () => {
    renderComponent();
    const deleteButton = screen.getByRole('button', { name: `Delete user ${mockUsers[0].email}` });
    fireEvent.click(deleteButton); // Click delete for the first user
    expect(onDelete).toHaveBeenCalledWith(mockUsers[0]);
  });
});
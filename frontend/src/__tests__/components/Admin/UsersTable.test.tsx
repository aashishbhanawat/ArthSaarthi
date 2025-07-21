import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import UsersTable from '../../../components/Admin/UsersTable';
import { User } from '../../../types/user';

const mockUsers: User[] = [
  { id: 1, email: 'admin@example.com', full_name: 'Admin User', is_active: true, is_admin: true },
  { id: 2, email: 'test@example.com', full_name: 'Test User', is_active: false, is_admin: false },
];

describe('UsersTable', () => {
  const onEdit = jest.fn();
  const onDelete = jest.fn();

  beforeEach(() => {
    render(<UsersTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);
  });

  test('renders table headers and user data correctly', () => {
    expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('Admin')).toBeInTheDocument();
    expect(screen.getByText('User')).toBeInTheDocument();
  });

  test('calls onEdit with the correct user when Edit button is clicked', () => {
    const editButtons = screen.getAllByRole('button', { name: 'Edit' });
    fireEvent.click(editButtons[1]); // Click edit for the second user
    expect(onEdit).toHaveBeenCalledWith(mockUsers[1]);
  });

  test('calls onDelete with the correct user when Delete button is clicked', () => {
    const deleteButtons = screen.getAllByRole('button', { name: 'Delete' });
    fireEvent.click(deleteButtons[0]); // Click delete for the first user
    expect(onDelete).toHaveBeenCalledWith(mockUsers[0]);
  });
});
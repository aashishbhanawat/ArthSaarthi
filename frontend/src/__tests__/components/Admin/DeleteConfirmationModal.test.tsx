import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DeleteConfirmationModal } from '../../../components/common/DeleteConfirmationModal';
import { User } from '../../../types/user';

const mockUser: User = {
  id: 'user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  is_active: true,
  is_admin: false,
  portfolios: [],
};

describe('DeleteConfirmationModal', () => {
  const onConfirm = jest.fn();
  const onClose = jest.fn();

  beforeEach(() => {
    // The common modal is tested by passing the title and message props directly
    render(
      <DeleteConfirmationModal
        isOpen={true}
        onClose={onClose}
        onConfirm={onConfirm}
        title="Delete User"
        message={<p>Are you sure you want to delete the user <strong>{mockUser.email}</strong>?</p>}
        isDeleting={false}
      />
    );
  });

  test('renders the confirmation message with the user name', () => {
    expect(screen.getByRole('heading', { name: 'Delete User' })).toBeInTheDocument();
    expect(screen.getByText(/are you sure you want to delete the user/i)).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
  });

  test('calls onConfirm when the Delete button is clicked', () => {
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Delete' }));
    expect(onConfirm).toHaveBeenCalled();
  });

  test('calls onClose when the Cancel button is clicked', () => {
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onClose).toHaveBeenCalled();
  });
});
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DeleteConfirmationModal } from '../../../components/common/DeleteConfirmationModal';
import { User } from '../../../types/user';

const mockUser: User = {
  id: 'user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  is_active: true,
  is_admin: false,
};

describe('DeleteConfirmationModal', () => {
  const onConfirm = jest.fn();
  const onClose = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = () => {
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
  };

  test('renders the confirmation message with the user name', () => {
    renderComponent();
    expect(screen.getByRole('heading', { name: 'Delete User' })).toBeInTheDocument();
    expect(screen.getByText(/are you sure you want to delete the user/i)).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
  });

  test('calls onConfirm when the Delete button is clicked', () => {
    renderComponent();
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Delete' }));
    expect(onConfirm).toHaveBeenCalled();
  });

  test('calls onClose when the Cancel button is clicked', () => {
    renderComponent();
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onClose).toHaveBeenCalled();
  });

  test('focuses the Cancel button when opened', async () => {
    renderComponent();
    const cancelButton = screen.getByRole('button', { name: 'Cancel' });
    await waitFor(() => {
        expect(cancelButton).toHaveFocus();
    });
  });

  test('has correct ARIA attributes', () => {
    renderComponent();
    const modal = screen.getByRole('dialog');
    const title = screen.getByRole('heading', { name: 'Delete User' });

    // Check aria-labelledby points to the title
    expect(modal).toHaveAttribute('aria-labelledby');
    expect(title).toHaveAttribute('id', modal.getAttribute('aria-labelledby'));

    // Check aria-describedby points to the message container
    expect(modal).toHaveAttribute('aria-describedby');
    // Note: The message is inside a div with the id that aria-describedby points to
    // We can verify the element with that ID exists and contains the text
    const descriptionId = modal.getAttribute('aria-describedby');
    // eslint-disable-next-line testing-library/no-node-access
    const descriptionElement = document.getElementById(descriptionId!);
    expect(descriptionElement).toBeInTheDocument();
    expect(descriptionElement).toHaveTextContent(/Are you sure you want to delete the user/);
  });
});

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Toast from '../../../components/common/Toast';

describe('Toast Component', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  it('renders success toast with correct accessibility attributes', () => {
    render(
      <Toast
        message="Operation successful"
        type="success"
        onClose={mockOnClose}
      />
    );

    const toast = screen.getByRole('status');
    expect(toast).toBeInTheDocument();
    expect(toast).toHaveTextContent('Operation successful');
    expect(toast).toHaveClass('bg-green-500');
    // Polite announcement for success
    // Note: jest-dom doesn't automatically check aria-live value with getByRole,
    // so we check attribute explicitly if needed, but getByRole('status') implies implicit aria behaviors.
    // However, explicitly checking attribute is good.
    expect(toast).toHaveAttribute('aria-live', 'polite');
  });

  it('renders error toast with correct accessibility attributes', () => {
    render(
      <Toast
        message="Operation failed"
        type="error"
        onClose={mockOnClose}
      />
    );

    const toast = screen.getByRole('alert');
    expect(toast).toBeInTheDocument();
    expect(toast).toHaveTextContent('Operation failed');
    expect(toast).toHaveClass('bg-red-500');
    // Assertive announcement for errors
    expect(toast).toHaveAttribute('aria-live', 'assertive');
  });

  it('renders close button with aria-label', () => {
    render(
      <Toast
        message="Test message"
        type="success"
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    expect(closeButton).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <Toast
        message="Test message"
        type="success"
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});

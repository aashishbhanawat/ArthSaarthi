import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Toast from '../../../components/common/Toast';

describe('Toast', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  it('renders success toast with correct role and message', () => {
    render(
      <Toast
        message="Operation successful"
        type="success"
        onClose={mockOnClose}
      />
    );

    const toastElement = screen.getByRole('status');
    expect(toastElement).toBeInTheDocument();
    expect(toastElement).toHaveTextContent('Operation successful');
    expect(toastElement).toHaveClass('bg-green-600');
  });

  it('renders error toast with correct role and message', () => {
    render(
      <Toast
        message="Operation failed"
        type="error"
        onClose={mockOnClose}
      />
    );

    const toastElement = screen.getByRole('alert');
    expect(toastElement).toBeInTheDocument();
    expect(toastElement).toHaveTextContent('Operation failed');
    expect(toastElement).toHaveClass('bg-red-600');
  });

  it('renders close button with accessible label', () => {
    render(
      <Toast
        message="Test message"
        type="success"
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByLabelText('Close notification');
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

    const closeButton = screen.getByLabelText('Close notification');
    fireEvent.click(closeButton);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});


import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AddAwardModal from '~/components/modals/AddAwardModal';
import { ToastProvider } from '~/context/ToastContext';

const queryClient = new QueryClient();

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
        <ToastProvider>
            {ui}
        </ToastProvider>
    </QueryClientProvider>
  );
};

describe('AddAwardModal', () => {
    const mockOnClose = jest.fn();

    it('renders the modal with the RSU form by default', () => {
        renderWithClient(
            <AddAwardModal
                portfolioId="test-portfolio-id"
                isOpen={true}
                onClose={mockOnClose}
            />
        );
        expect(screen.getByText('Add ESPP/RSU Award')).toBeInTheDocument();
        expect(screen.getByLabelText('RSU Vest')).toBeChecked();
    });

    it('switches to the ESPP form when the ESPP radio button is clicked', () => {
        renderWithClient(
            <AddAwardModal
                portfolioId="test-portfolio-id"
                isOpen={true}
                onClose={mockOnClose}
            />
        );
        fireEvent.click(screen.getByLabelText('ESPP Purchase'));
        expect(screen.getByLabelText('ESPP Purchase')).toBeChecked();
    });

    it('shows the "Sell to Cover" fields when the checkbox is checked', () => {
        renderWithClient(
            <AddAwardModal
                portfolioId="test-portfolio-id"
                isOpen={true}
                onClose={mockOnClose}
            />
        );
        fireEvent.click(screen.getByLabelText("Record 'Sell to Cover' for taxes"));
        expect(screen.getByLabelText('Shares Sold')).toBeInTheDocument();
        expect(screen.getByLabelText('Sale Price (USD)')).toBeInTheDocument();
    });
});

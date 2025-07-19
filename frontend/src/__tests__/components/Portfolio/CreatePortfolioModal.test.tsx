import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import CreatePortfolioModal from '../../../components/Portfolio/CreatePortfolioModal';
import * as usePortfoliosHook from '../../../hooks/usePortfolios';

const queryClient = new QueryClient();
const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('CreatePortfolioModal', () => {
    const mockOnClose = jest.fn();
    const mockCreatePortfolio = jest.fn();

    beforeEach(() => {
        jest.spyOn(usePortfoliosHook, 'useCreatePortfolio').mockReturnValue({
            mutate: mockCreatePortfolio,
            isPending: false,
            isSuccess: false,
            isError: false,
            reset: jest.fn(),
        } as any);
    });

    it('does not render when isOpen is false', () => {
        render(<CreatePortfolioModal isOpen={false} onClose={mockOnClose} />, { wrapper });
        expect(screen.queryByRole('heading', { name: /create new portfolio/i })).not.toBeInTheDocument();
    });

    it('renders the form when isOpen is true', () => {
        render(<CreatePortfolioModal isOpen={true} onClose={mockOnClose} />, { wrapper });
        expect(screen.getByRole('heading', { name: /create new portfolio/i })).toBeInTheDocument();
        expect(screen.getByLabelText(/portfolio name/i)).toBeInTheDocument();
    });

    it('calls the create mutation on form submission', async () => {
        render(<CreatePortfolioModal isOpen={true} onClose={mockOnClose} />, { wrapper });
        
        await userEvent.type(screen.getByLabelText(/portfolio name/i), 'My New Portfolio');
        await userEvent.click(screen.getByRole('button', { name: /create/i }));

        await waitFor(() => {
            expect(mockCreatePortfolio).toHaveBeenCalledWith({ name: 'My New Portfolio' });
        });
    });

    it('calls onClose when cancel button is clicked', async () => {
        render(<CreatePortfolioModal isOpen={true} onClose={mockOnClose} />, { wrapper });
        await userEvent.click(screen.getByRole('button', { name: /cancel/i }));
        expect(mockOnClose).toHaveBeenCalled();
    });

    it('closes the modal on successful creation', async () => {
        jest.spyOn(usePortfoliosHook, 'useCreatePortfolio').mockReturnValue({
            mutate: mockCreatePortfolio, isSuccess: true, isPending: false, isError: false, reset: jest.fn()
        } as any);
        render(<CreatePortfolioModal isOpen={true} onClose={mockOnClose} />, { wrapper });
        expect(mockOnClose).toHaveBeenCalled();
    });
});
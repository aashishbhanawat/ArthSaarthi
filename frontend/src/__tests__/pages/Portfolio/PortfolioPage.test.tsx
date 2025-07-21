import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import PortfolioPage from '../../../pages/Portfolio/PortfolioPage';
import * as usePortfoliosHook from '../../../hooks/usePortfolios';
import { Portfolio } from '../../../types/portfolio';

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
        <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
);

const mockPortfolios: Portfolio[] = [
    { id: 1, name: 'Retirement Fund', user_id: 1, transactions: [] },
    { id: 2, name: 'Vacation Fund', user_id: 1, transactions: [] },
];

describe('PortfolioPage', () => {
    it('shows a loading state initially', () => {
        jest.spyOn(usePortfoliosHook, 'usePortfolios').mockReturnValue({
            data: undefined,
            isLoading: true,
            isError: false,
        } as any);

        render(<PortfolioPage />, { wrapper });
        expect(screen.getByText(/loading portfolios.../i)).toBeInTheDocument();
    });

    it('shows an error message if fetching fails', () => {
        jest.spyOn(usePortfoliosHook, 'usePortfolios').mockReturnValue({
            data: undefined,
            isLoading: false,
            isError: true,
            error: new Error('Failed to fetch'),
        } as any);

        render(<PortfolioPage />, { wrapper });
        expect(screen.getByText(/error: failed to fetch/i)).toBeInTheDocument();
    });

    it('renders a list of portfolios on successful fetch', () => {
        jest.spyOn(usePortfoliosHook, 'usePortfolios').mockReturnValue({
            data: mockPortfolios,
            isLoading: false,
            isError: false,
        } as any);

        render(<PortfolioPage />, { wrapper });
        expect(screen.getByText('Retirement Fund')).toBeInTheDocument();
        expect(screen.getByText('Vacation Fund')).toBeInTheDocument();
    });

    it('opens the create portfolio modal when the "Create New Portfolio" button is clicked', async () => {
        jest.spyOn(usePortfoliosHook, 'usePortfolios').mockReturnValue({
            data: [],
            isLoading: false,
            isError: false,
        } as any);

        render(<PortfolioPage />, { wrapper });
        
        await userEvent.click(screen.getByRole('button', { name: /create new portfolio/i }));

        await waitFor(() => expect(screen.getByRole('heading', { name: /create new portfolio/i })).toBeInTheDocument());
    });
});
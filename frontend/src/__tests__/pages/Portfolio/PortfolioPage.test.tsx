import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import PortfolioPage from '../../../pages/Portfolio/PortfolioPage';
import * as usePortfoliosHook from '../../../hooks/usePortfolios';
import { Portfolio } from '../../../types/portfolio';

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
        <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            {children}
        </MemoryRouter>
    </QueryClientProvider>
);

const mockPortfolios: Portfolio[] = [
    { id: '1', name: 'Retirement Fund', description: 'My retirement fund', transactions: [] },
    { id: '2', name: 'Vacation Fund', description: 'My vacation fund', transactions: [] },
];

const mockUsePortfolios = (data: Partial<ReturnType<typeof usePortfoliosHook.usePortfolios>>) => {
    return jest.spyOn(usePortfoliosHook, 'usePortfolios').mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
        error: null,
        ...data,
    } as ReturnType<typeof usePortfoliosHook.usePortfolios>);
};

describe('PortfolioPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('shows a loading state initially', () => {
        mockUsePortfolios({ data: undefined, isLoading: true });
        render(<PortfolioPage />, { wrapper });
        expect(screen.getByText(/loading portfolios.../i)).toBeInTheDocument();
    });

    it('shows an error message if fetching fails', () => {
        mockUsePortfolios({ isError: true, error: new Error('Failed to fetch') });
        render(<PortfolioPage />, { wrapper });
        expect(screen.getByText(/error: failed to fetch/i)).toBeInTheDocument();
    });

    it('renders a list of portfolios on successful fetch', () => {
        mockUsePortfolios({ data: mockPortfolios });
        render(<PortfolioPage />, { wrapper });
        expect(screen.getByText('Retirement Fund')).toBeInTheDocument();
        expect(screen.getByText('Vacation Fund')).toBeInTheDocument();
    });

    it('opens the create portfolio modal when the "Create New Portfolio" button is clicked', async () => {
        mockUsePortfolios({ data: [] });
        render(<PortfolioPage />, { wrapper });
        
        await userEvent.click(screen.getByRole('button', { name: /create new portfolio/i }));

        const modalTitle = await screen.findByRole('heading', { name: /create new portfolio/i });
        expect(modalTitle).toBeInTheDocument();
    });
});
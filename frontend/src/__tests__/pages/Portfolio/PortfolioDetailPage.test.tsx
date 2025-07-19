import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import PortfolioDetailPage from '../../../pages/Portfolio/PortfolioDetailPage';
import * as usePortfoliosHook from '../../../hooks/usePortfolios';
import { Portfolio } from '../../../types/portfolio';

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockPortfolio: Portfolio = {
    id: 1,
    name: 'Tech Investments',
    user_id: 1,
    transactions: [
        {
            id: 1,
            transaction_type: 'BUY',
            quantity: '10',
            price_per_unit: '150.00',
            fees: '5.00',
            transaction_date: new Date().toISOString(),
            asset: { id: 1, ticker_symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'STOCK', currency: 'USD' },
        },
    ],
};

describe('PortfolioDetailPage', () => {
    beforeEach(() => {
        jest.spyOn(usePortfoliosHook, 'usePortfolio').mockReturnValue({
            data: mockPortfolio,
            isLoading: false,
            isError: false,
        } as any);
    });

    const renderComponent = () => {
        render(
            <MemoryRouter initialEntries={['/portfolios/1']}>
                <Routes>
                    <Route path="/portfolios/:id" element={<PortfolioDetailPage />} />
                </Routes>
            </MemoryRouter>,
            { wrapper }
        );
    };

    it('renders the portfolio name and transaction list', () => {
        renderComponent();
        expect(screen.getByRole('heading', { name: 'Tech Investments' })).toBeInTheDocument();
        expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    });

    it('opens the add transaction modal when the button is clicked', async () => {
        renderComponent();
        await userEvent.click(screen.getByRole('button', { name: /add transaction/i }));
        await waitFor(() => expect(screen.getByRole('heading', { name: /add new transaction/i })).toBeInTheDocument());
    });
});
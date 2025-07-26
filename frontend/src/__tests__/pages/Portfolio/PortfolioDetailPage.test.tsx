import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import PortfolioDetailPage from '../../../pages/Portfolio/PortfolioDetailPage';
import * as portfolioHooks from '../../../hooks/usePortfolios';
import { Portfolio } from '../../../types';

jest.mock('../../../hooks/usePortfolios');
const { usePortfolio, useCreateTransaction, useCreateAsset } = portfolioHooks as jest.Mocked<typeof portfolioHooks>;

// Default mocks for hooks used by the modal
const mockMutateTransaction = jest.fn();
const mockMutateAsset = jest.fn();

const queryClient = new QueryClient();

const mockPortfolio: Portfolio = {
    id: 1,
    name: 'Tech Investments',
    description: 'My tech stock portfolio',
    user_id: 1,
    transactions: [
        {
            id: 1,
            asset_id: 1,
            portfolio_id: 1,
            transaction_type: 'BUY',
            quantity: 10,
            price_per_unit: 150,
            transaction_date: '2025-07-25T12:00:00Z',
            fees: 5,
            asset: { id: 1, ticker_symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'Stock', currency: 'USD', exchange: 'NASDAQ' },
        },
    ],
};

const renderComponent = () => {
    render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter initialEntries={['/portfolios/1']}>
                <Routes>
                    <Route path="/portfolios/:id" element={<PortfolioDetailPage />} />
                </Routes>
            </MemoryRouter>
        </QueryClientProvider>
    );
};

describe('PortfolioDetailPage', () => {
    beforeEach(() => {
        usePortfolio.mockReturnValue({
            data: mockPortfolio,
            isLoading: false,
            isError: false,
        });
        // @ts-ignore
        useCreateTransaction.mockReturnValue({ mutate: mockMutateTransaction, isPending: false });
        // @ts-ignore
        useCreateAsset.mockReturnValue({ mutate: mockMutateAsset, isPending: false });
    });

    it('opens the add transaction modal when the button is clicked', async () => {
        renderComponent();
        await userEvent.click(screen.getByRole('button', { name: /add transaction/i }));
        await waitFor(() => expect(screen.getByRole('heading', { name: /add transaction/i })).toBeInTheDocument());
    });
});
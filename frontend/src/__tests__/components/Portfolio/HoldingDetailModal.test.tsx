import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import HoldingDetailModal from '../../../components/Portfolio/HoldingDetailModal';
import * as portfolioHooks from '../../../hooks/usePortfolios';
import { Holding } from '../../../types/holding';
import { Transaction } from '../../../types/portfolio';

jest.mock('../../../hooks/usePortfolios');
const mockedPortfolioHooks = portfolioHooks as jest.Mocked<typeof portfolioHooks>;

const mockHolding: Holding = {
    asset_id: 'a-1',
    ticker_symbol: "AAPL",
    asset_name: "Apple Inc.",
    quantity: 50, // Corrected to match mockTransactions: 50 buy - 50 sell + 50 buy = 50
    average_buy_price: 120,
    total_invested_amount: 12000,
    current_price: 150,
    current_value: 15000,
    days_pnl: 250,
    days_pnl_percentage: 1.69,
    unrealized_pnl: 3000,
    unrealized_pnl_percentage: 25,
};

const mockTransactions: Transaction[] = [
    // This first BUY should be completely consumed by the SELL
    { id: 't-1', portfolio_id: 'p-1', asset_id: 'a-1', transaction_type: 'BUY', quantity: 50, price_per_unit: 110, fees: 5, transaction_date: '2023-01-10T10:00:00', user_id: 'u-1' },
    { id: 't-2', portfolio_id: 'p-1', asset_id: 'a-1', transaction_type: 'SELL', quantity: 50, price_per_unit: 140, fees: 2, transaction_date: '2023-02-10T10:00:00', user_id: 'u-1' },
    // This second BUY should be the only one remaining
    { id: 't-3', portfolio_id: 'p-1', asset_id: 'a-1', transaction_type: 'BUY', quantity: 50, price_per_unit: 130, fees: 5, transaction_date: '2023-03-15T10:00:00', user_id: 'u-1' },
];

const queryClient = new QueryClient();

const renderComponent = () => {
    return render(
        <QueryClientProvider client={queryClient}>
            <HoldingDetailModal holding={mockHolding} portfolioId="p-1" onClose={jest.fn()} />
        </QueryClientProvider>
    );
};

describe('HoldingDetailModal', () => {
    const MOCK_TODAY = new Date('2024-01-10T10:00:00Z');

    beforeAll(() => {
        jest.useFakeTimers().setSystemTime(MOCK_TODAY);
    });

    afterAll(() => {
        jest.useRealTimers();
    });

    it('renders loading state initially', () => {
        mockedPortfolioHooks.useAssetTransactions.mockReturnValue({
            data: undefined,
            isLoading: true,
            error: null,
        } as any);
        renderComponent();
        expect(screen.getByText('Loading transactions...')).toBeInTheDocument();
    });

    it('renders error state', () => {
        mockedPortfolioHooks.useAssetTransactions.mockReturnValue({
            data: undefined,
            isLoading: false,
            error: new Error('Failed to fetch'),
        } as any);
        renderComponent();
        expect(screen.getByText('Error loading transactions: Failed to fetch')).toBeInTheDocument();
    });

    it('renders holding details and transaction list on successful fetch', async () => {
        mockedPortfolioHooks.useAssetTransactions.mockReturnValue({
            data: mockTransactions,
            isLoading: false,
            error: null,
        } as any);
        renderComponent();

        // Check holding summary details
        expect(screen.getByText('Apple Inc. (AAPL)')).toBeInTheDocument();
        // The number '50' appears twice (summary quantity and table quantity).
        // We need a more specific query to avoid ambiguity.
        const allFiftyElements = screen.getAllByText('50');
        const summaryQuantity = allFiftyElements.find(el => el.tagName.toLowerCase() === 'p');
        expect(summaryQuantity).toBeInTheDocument();
        expect(screen.getByText('₹120.00')).toBeInTheDocument(); // Avg Buy Price
        expect(screen.getByText('₹15,000.00')).toBeInTheDocument(); // Current Value
        expect(screen.getByText('₹3,000.00')).toBeInTheDocument(); // Unrealized P&L

        // Check for transaction table headers
        expect(screen.getByText('Date')).toBeInTheDocument();
        expect(screen.getByText('CAGR %')).toBeInTheDocument();

        // Check for transaction data using FIFO logic
        await waitFor(() => {
            // The first BUY transaction from Jan 10 should NOT be visible due to FIFO
            expect(screen.queryByText('10 Jan 2023')).not.toBeInTheDocument();

            // The second BUY transaction from Mar 15 should be the only one visible
            expect(screen.getByText('15 Mar 2023')).toBeInTheDocument();
            expect(screen.getByText('₹6,500.00')).toBeInTheDocument(); // Total value of the second transaction
        });
    });
});
import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import HoldingsTable from '../../../components/Portfolio/HoldingsTable';
import { Holding } from '../../../types/holding';

const mockHoldings: Holding[] = [
    {
        asset_id: 'asset-1',
        ticker_symbol: 'AAPL',
        asset_name: 'Apple Inc.',
        quantity: 10,
        average_buy_price: 150,
        total_invested_amount: 1500,
        current_price: 175,
        current_value: 1750,
        days_pnl: 50,
        days_pnl_percentage: 2.94,
        unrealized_pnl: 250,
        unrealized_pnl_percentage: 16.67,
    },
    {
        asset_id: 'asset-2',
        ticker_symbol: 'GOOGL',
        asset_name: 'Alphabet Inc.',
        quantity: 5,
        average_buy_price: 2800,
        total_invested_amount: 14000,
        current_price: 2750,
        current_value: 13750,
        days_pnl: -100,
        days_pnl_percentage: -3.57,
        unrealized_pnl: -250,
        unrealized_pnl_percentage: -1.79,
    },
];

describe('HoldingsTable', () => {
    it('renders loading state correctly', () => {
        render(<HoldingsTable holdings={undefined} isLoading={true} error={null} onRowClick={jest.fn()} />);
        expect(screen.getByText('', { selector: '.animate-pulse' })).toBeInTheDocument();
    });

    it('renders error state correctly', () => {
        render(<HoldingsTable holdings={undefined} isLoading={false} error={new Error('Failed to fetch')} onRowClick={jest.fn()} />);
        expect(screen.getByText('Error loading holdings: Failed to fetch')).toBeInTheDocument();
    });

    it('renders empty state when no holdings are provided', () => {
        render(<HoldingsTable holdings={[]} isLoading={false} error={null} onRowClick={jest.fn()} />);
        expect(screen.getByText('You have no current holdings in this portfolio.')).toBeInTheDocument();
    });

    it('renders table with holdings data correctly', () => {
        render(<HoldingsTable holdings={mockHoldings} isLoading={false} error={null} onRowClick={jest.fn()} />);

        // Check for headers
        expect(screen.getByText('Holdings')).toBeInTheDocument();
        expect(screen.getByText('Asset')).toBeInTheDocument();
        expect(screen.getByText('Avg. Buy Price')).toBeInTheDocument();

        // Check for data from both mock holdings
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
        expect(screen.getByText('GOOGL')).toBeInTheDocument();
        expect(screen.getByText('Alphabet Inc.')).toBeInTheDocument();

        // Check for a formatted currency value
        expect(screen.getByText('₹1,750.00')).toBeInTheDocument(); // AAPL current_value
    });

    it('applies correct colors for P&L values', () => {
        render(<HoldingsTable holdings={mockHoldings} isLoading={false} error={null} onRowClick={jest.fn()} />);

        // Positive P&L for AAPL should be green
        expect(screen.getByText('₹250.00')).toHaveClass('text-green-600');

        // Negative P&L for GOOGL should be red
        expect(screen.getByText('-₹250.00')).toHaveClass('text-red-600');
        expect(screen.getByText('-1.79%')).toHaveClass('text-red-600');
    });

    it('sorts the table when a column header is clicked', () => {
        render(<HoldingsTable holdings={mockHoldings} isLoading={false} error={null} onRowClick={jest.fn()} />);

        // Default sort is by Current Value desc. GOOGL (13750) > AAPL (1750)
        let rows = screen.getAllByRole('row');
        // The first row is the header, so we check from index 1
        expect(within(rows[1]).getByText('GOOGL')).toBeInTheDocument();
        expect(within(rows[2]).getByText('AAPL')).toBeInTheDocument();

        // Click on 'Asset' header to sort by ticker_symbol ascending
        const assetHeader = screen.getByText(/Asset/);
        fireEvent.click(assetHeader);

        rows = screen.getAllByRole('row');
        // Now AAPL should be first
        expect(within(rows[1]).getByText('AAPL')).toBeInTheDocument();
        expect(within(rows[2]).getByText('GOOGL')).toBeInTheDocument();
        expect(screen.getByText(/Asset\s*▲/)).toBeInTheDocument();

        // Click on 'Asset' header again to sort descending
        fireEvent.click(assetHeader);
        rows = screen.getAllByRole('row');
        expect(within(rows[1]).getByText('GOOGL')).toBeInTheDocument();
        expect(within(rows[2]).getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText(/Asset\s*▼/)).toBeInTheDocument();
    });
});
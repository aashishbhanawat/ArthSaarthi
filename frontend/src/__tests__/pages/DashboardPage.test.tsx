import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import DashboardPage from '../../pages/DashboardPage';
import { useDashboardSummary } from '../../hooks/useDashboard';
import { DashboardSummary } from '../../types/dashboard';

// Mock the hook
jest.mock('../../hooks/useDashboard');

const mockUseDashboardSummary = useDashboardSummary as jest.Mock;

describe('DashboardPage', () => {
    it('should render loading state', () => {
        mockUseDashboardSummary.mockReturnValue({
            isLoading: true,
            isError: false,
            error: null,
            data: null,
        });

        render(<DashboardPage />);
        expect(screen.getByText('Loading dashboard data...')).toBeInTheDocument();
    });

    it('should render error state', () => {
        mockUseDashboardSummary.mockReturnValue({
            isLoading: false,
            isError: true,
            error: new Error('Failed to fetch dashboard'),
            data: null,
        });

        render(<DashboardPage />);
        expect(screen.getByText('Error: Failed to fetch dashboard')).toBeInTheDocument();
    });

    it('should render dashboard with data on success', () => {
        const mockSummary: DashboardSummary = {
            total_value: '12345.67',
            total_unrealized_pnl: '123.45',
            total_realized_pnl: '-50.00',
            top_movers: [],
        };

        mockUseDashboardSummary.mockReturnValue({
            isLoading: false,
            isError: false,
            error: null,
            data: mockSummary,
        });

        render(<DashboardPage />);

        // Check for titles
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Total Value')).toBeInTheDocument();
        expect(screen.getByText('Unrealized P/L')).toBeInTheDocument();
        expect(screen.getByText('Realized P/L')).toBeInTheDocument();

        // Check for formatted values
        expect(screen.getByText('$12,345.67')).toBeInTheDocument();
        expect(screen.getByText('$123.45')).toBeInTheDocument();
        expect(screen.getByText('-$50.00')).toBeInTheDocument();
    });

    it('should render top movers table with no data message when top_movers is empty', () => {
        mockUseDashboardSummary.mockReturnValue({
            isLoading: false, isError: false, error: null, data: { total_value: '1000', total_unrealized_pnl: '0', total_realized_pnl: '0', top_movers: [] }
        });
        render(<DashboardPage />);
        expect(screen.getByText('No market data available.')).toBeInTheDocument();
    });
});
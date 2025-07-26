import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardPage from '../../pages/DashboardPage';
import * as useDashboard from '../../hooks/useDashboard';
import { DashboardSummary } from '../../types/dashboard';

// This mock factory pattern is required to avoid Jest's hoisting issues with JSX
jest.mock('../../components/Dashboard/PortfolioHistoryChart', () => function MockPortfolioHistoryChart() {
  return <div data-testid="line-chart-mock" />;
});
jest.mock('../../components/Dashboard/AssetAllocationChart', () => function MockAssetAllocationChart() {
  return <div data-testid="pie-chart-mock" />;
});

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockSummary: DashboardSummary = {
  total_value: 12345.67,
  total_unrealized_pnl: 123.45,
  total_realized_pnl: -50.00,
  top_movers: [],
  asset_allocation: [],
};

describe('DashboardPage', () => {
  it('should render loading state initially', () => {
    jest.spyOn(useDashboard, 'useDashboardSummary').mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    } as any);

    render(<DashboardPage />, { wrapper });
    expect(screen.getByText('Loading dashboard data...')).toBeInTheDocument();
  });

  it('should render error state', () => {
    jest.spyOn(useDashboard, 'useDashboardSummary').mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Failed to fetch'),
    } as any);

    render(<DashboardPage />, { wrapper });
    expect(screen.getByText('Error: Failed to fetch')).toBeInTheDocument();
  });

  it('should render dashboard with data on success', () => {
    jest.spyOn(useDashboard, 'useDashboardSummary').mockReturnValue({
      data: mockSummary,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<DashboardPage />, { wrapper });

    // Check for formatted values
    expect(screen.getByText('₹12,345.67')).toBeInTheDocument();
    expect(screen.getByText('₹123.45')).toBeInTheDocument();
    expect(screen.getByText('-₹50.00')).toBeInTheDocument();
  });

  it('should render top movers table with no data message when top_movers is empty', () => {
    jest.spyOn(useDashboard, 'useDashboardSummary').mockReturnValue({
      data: { ...mockSummary, top_movers: [] },
      isLoading: false,
      isError: false,
      error: null,
    } as any);
    render(<DashboardPage />, { wrapper });
    expect(screen.getByText('No market data available')).toBeInTheDocument();
  });
});
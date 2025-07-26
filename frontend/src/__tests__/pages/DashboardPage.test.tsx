import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import DashboardPage from '../../pages/DashboardPage';
import {
  useDashboardSummary,
  useDashboardHistory,
  useDashboardAllocation,
} from '../../hooks/useDashboard';

// Mock the hook
jest.mock('../../hooks/useDashboard');
jest.mock('react-chartjs-2', () => {
  const React = require('react');
  return {
    Line: () => React.createElement('div', { 'data-testid': 'line-chart-mock' }),
    Pie: () => React.createElement('div', { 'data-testid': 'pie-chart-mock' }),
  };
});

const mockUseDashboardSummary = useDashboardSummary as jest.Mock;
const mockUseDashboardHistory = useDashboardHistory as jest.Mock;
const mockUseDashboardAllocation = useDashboardAllocation as jest.Mock;

describe('DashboardPage', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();

    // Provide default successful mocks for all hooks used in the component tree
    mockUseDashboardSummary.mockReturnValue({
      isLoading: false,
      isError: false,
      error: null,
      data: {
        total_value: 12345.67,
        total_unrealized_pnl: 123.45,
        total_realized_pnl: -50.0,
        top_movers: [],
        asset_allocation: [],
      },
    });

    mockUseDashboardHistory.mockReturnValue({
      isLoading: false,
      isError: false,
      error: null,
      data: { history: [] },
    });

    mockUseDashboardAllocation.mockReturnValue({
      isLoading: false,
      isError: false,
      error: null,
      data: { allocation: [] },
    });
  });

  it('should render loading state', () => {
    mockUseDashboardSummary.mockReturnValue({ isLoading: true });
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
    render(<DashboardPage />);

    // Check for titles
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Portfolio History')).toBeInTheDocument();
    expect(screen.getByText('Asset Allocation')).toBeInTheDocument();

    // Check for formatted values
    expect(screen.getByText('$12,345.67')).toBeInTheDocument();
    expect(screen.getByText('$123.45')).toBeInTheDocument();
    expect(screen.getByText('-$50.00')).toBeInTheDocument();
  });

  it('should render top movers table with no data message when top_movers is empty', () => {
    mockUseDashboardSummary.mockReturnValue({
      isLoading: false, isError: false, error: null, data: { total_value: 1000, total_unrealized_pnl: 0, total_realized_pnl: 0, top_movers: [], asset_allocation: [] }
    });
    render(<DashboardPage />);
    expect(screen.getByText('No market data available.')).toBeInTheDocument();
  });
});
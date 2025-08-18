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
jest.mock('../../components/Dashboard/PortfolioHistoryChart', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return function DummyPortfolioHistoryChart() {
    return React.createElement('div', { 'data-testid': 'portfolio-history-chart-mock' });
  };
});
jest.mock('../../components/Dashboard/AssetAllocationChart', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return function DummyAssetAllocationChart() {
    return React.createElement('div', { 'data-testid': 'asset-allocation-chart-mock' });
  };
});
jest.mock('../../components/HelpLink', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return function DummyHelpLink({ sectionId }: { sectionId: string }) {
    return React.createElement('a', { href: `/user_guide.md#${sectionId}` }, '?');
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
    expect(screen.getByText('Error loading dashboard data.')).toBeInTheDocument();
  });

  it('should render dashboard with data on success', () => {
    render(<DashboardPage />);

    // Check for main title
    expect(screen.getByText('Dashboard')).toBeInTheDocument();

    // Check for section titles. Use getAllByText because some child components might also have titles.
    // We just care that the titles rendered by DashboardPage are present.
    expect(screen.getAllByText('Portfolio History')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Asset Allocation')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Top Movers')[0]).toBeInTheDocument();

    // Check for formatted values
    expect(screen.getByText('₹12,345.67')).toBeInTheDocument();
    expect(screen.getByText('₹123.45')).toBeInTheDocument();
    expect(screen.getByText('-₹50.00')).toBeInTheDocument();

    // Check that chart mocks are rendered
    expect(screen.getByTestId('portfolio-history-chart-mock')).toBeInTheDocument();
    expect(screen.getByTestId('asset-allocation-chart-mock')).toBeInTheDocument();
  });

  it('should render top movers table with no data message when top_movers is empty', () => {
    mockUseDashboardSummary.mockReturnValue({
      isLoading: false, isError: false, error: null, data: { total_value: 1000, total_unrealized_pnl: 0, total_realized_pnl: 0, top_movers: [], asset_allocation: [] }
    });
    render(<DashboardPage />);
    expect(screen.getByText('No market data available')).toBeInTheDocument();
  });
});
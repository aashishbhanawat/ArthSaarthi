import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider, UseQueryResult } from '@tanstack/react-query';
import PortfolioDetailPage from '../../../pages/Portfolio/PortfolioDetailPage';
import * as portfolioHooks from '../../../hooks/usePortfolios';
import { Portfolio } from '../../../types/portfolio';
import { Holding, PortfolioSummary } from '../../../types/holding';
import { PortfolioAnalytics } from '../../../types/analytics';

jest.mock('../../../hooks/usePortfolios');
const mockedPortfolioHooks = portfolioHooks as jest.Mocked<typeof portfolioHooks>;

jest.mock('../../../components/Portfolio/TransactionFormModal', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  // The new modal doesn't receive transactionToEdit
  return ({ onClose }: { onClose: () => void }) =>
    React.createElement('div', { 'data-testid': 'transaction-form-modal' },
      React.createElement('h2', { role: 'heading' }, 'Add Transaction'),
      React.createElement('button', { onClick: onClose }, 'Close')
    );
});

jest.mock('../../../components/Portfolio/AddAwardModal', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return ({ onClose }: { onClose: () => void }) =>
    React.createElement('div', { 'data-testid': 'add-award-modal' },
      React.createElement('h2', { role: 'heading' }, 'Add ESPP/RSU Award'),
      React.createElement('button', { onClick: onClose }, 'Close')
    );
});

// Mock child components to isolate the page component logic
jest.mock('../../../components/Portfolio/PortfolioSummary', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return () => React.createElement('div', { 'data-testid': 'portfolio-summary' });
});
jest.mock('../../../components/Portfolio/HoldingsTable', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  // The mock needs to be able to trigger the onRowClick prop
  return (props: { onRowClick: (holding: Holding) => void }) =>
    React.createElement('div', {
      'data-testid': 'holdings-table',
      onClick: () => props.onRowClick(mockHoldings[0]) // Simulate clicking the first holding
    });
});
jest.mock('../../../components/Portfolio/AnalyticsCard', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  return () => React.createElement('div', { 'data-testid': 'analytics-card' });
});
jest.mock('../../../components/Portfolio/HoldingDetailModal', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require('react');
  // Mock the modal to verify it opens and can be closed
  return ({ holding, onClose }: { holding: Holding, onClose: () => void }) => React.createElement('div', { 'data-testid': 'holding-detail-modal' }, `Details for ${holding.ticker_symbol}`, React.createElement('button', { onClick: onClose }, 'Close Modal'));
});

const queryClient = new QueryClient();

const mockPortfolio: Portfolio = {
  id: 'p-1',
  name: 'Tech Investments',
  description: 'My tech stock portfolio',
  transactions: [], // Not used directly by the new page
};

const mockSummary: PortfolioSummary = {
  total_value: 15000,
  total_invested_amount: 12000,
  days_pnl: 250,
  total_unrealized_pnl: 3000,
  total_realized_pnl: 500,
};

const mockHoldings: Holding[] = [{ // This needs to be accessible to the HoldingsTable mock
  asset_id: "a-1",
  ticker_symbol: "AAPL",
  asset_name: "Apple Inc.",
  quantity: 100,
  average_buy_price: 120,
  total_invested_amount: 12000,
  current_price: 150,
  current_value: 15000,
  days_pnl: 250,
  days_pnl_percentage: 1.69,
  unrealized_pnl: 3000,
  unrealized_pnl_percentage: 25,
}];

const renderComponent = () => {
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/portfolios/p-1']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/portfolios/:id" element={<PortfolioDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('PortfolioDetailPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedPortfolioHooks.usePortfolio.mockReturnValue({ data: mockPortfolio, isLoading: false, isError: false } as UseQueryResult<Portfolio, Error>);
    mockedPortfolioHooks.usePortfolioSummary.mockReturnValue({ data: mockSummary, isLoading: false, error: null } as UseQueryResult<PortfolioSummary, Error>);
    mockedPortfolioHooks.usePortfolioHoldings.mockReturnValue({ data: { holdings: mockHoldings }, isLoading: false, error: null } as UseQueryResult<{ holdings: Holding[] }, Error>);
    mockedPortfolioHooks.usePortfolioAnalytics.mockReturnValue({ data: {} as PortfolioAnalytics, isLoading: false, isError: false } as UseQueryResult<PortfolioAnalytics, Error>);
    mockedPortfolioHooks.useDiversification.mockReturnValue({ data: undefined, isLoading: false, isError: false } as UseQueryResult<unknown, Error>);
    mockedPortfolioHooks.useBenchmarkComparison.mockReturnValue({
      data: { portfolio_xirr: 0, benchmark_xirr: 0, chart_data: [] },
      isLoading: false,
      error: null
    } as UseQueryResult<any, Error>);
  });

  it('renders the portfolio name and child components', () => {
    renderComponent();
    expect(screen.getByText('Tech Investments')).toBeInTheDocument();
    expect(screen.getByTestId('portfolio-summary')).toBeInTheDocument();
    expect(screen.getByTestId('analytics-card')).toBeInTheDocument();
    expect(screen.getByTestId('holdings-table')).toBeInTheDocument();
  });

  it('opens the add transaction modal when the "Add Transaction" button is clicked', async () => {
    renderComponent();
    await userEvent.click(screen.getByRole('button', { name: /add transaction/i }));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Add Transaction' })).toBeInTheDocument();
    });
  });

  it('opens the add award modal when the "Add ESPP/RSU Award" dropdown item is clicked', async () => {
    renderComponent();
    // Use the aria-label to target the toggle button specifically
    await userEvent.click(screen.getByLabelText('Additional actions'));
    const awardOption = await screen.findByText('Add ESPP/RSU Award');
    await userEvent.click(awardOption);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Add ESPP/RSU Award' })).toBeInTheDocument();
    });
  });

  it('opens and closes the holding detail modal when a holding is clicked', async () => {
    renderComponent();

    // Modal should not be visible initially
    expect(screen.queryByTestId('holding-detail-modal')).not.toBeInTheDocument();

    // Simulate a click on our mocked holdings table
    fireEvent.click(screen.getByTestId('holdings-table'));

    // The modal should now be visible with the correct holding's data
    const modal = await screen.findByTestId('holding-detail-modal');
    expect(modal).toBeInTheDocument();
    expect(screen.getByText('Details for AAPL')).toBeInTheDocument();

    // Click the close button inside the mocked modal
    fireEvent.click(screen.getByRole('button', { name: 'Close Modal' }));
    expect(screen.queryByTestId('holding-detail-modal')).not.toBeInTheDocument();
  });

  it('displays loading state correctly', () => {
    mockedPortfolioHooks.usePortfolio.mockReturnValue({ data: undefined, isLoading: true, isError: false } as UseQueryResult<Portfolio, Error>);
    renderComponent();
    expect(screen.getByText('Loading portfolio details...')).toBeInTheDocument();
  });

  it('displays error state correctly', () => {
    mockedPortfolioHooks.usePortfolio.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Failed to fetch'),
    } as UseQueryResult<Portfolio, Error>);
    renderComponent();
    expect(screen.getByText('Error: Failed to fetch')).toBeInTheDocument();
  });

  it('displays not found message if portfolio is not found', () => {
    mockedPortfolioHooks.usePortfolio.mockReturnValue({ data: undefined, isLoading: false, isError: false } as UseQueryResult<Portfolio, Error>);
    renderComponent();
    expect(screen.getByText('Portfolio not found.')).toBeInTheDocument();
  });
});

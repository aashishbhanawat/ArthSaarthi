import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import HoldingDetailModal from '../../../components/Portfolio/HoldingDetailModal';
import * as portfolioHooks from '../../../hooks/usePortfolios';
import { Holding } from '../../../types/holding';
import { Transaction } from '../../../types/portfolio';

const mockHolding: Holding = {
  asset_id: 'asset-1',
  asset_name: 'Test Asset',
  ticker_symbol: 'TEST',
  quantity: 100,
  average_buy_price: 150,
  current_price: 160,
  current_value: 16000,
  unrealized_pnl: 1000,
  asset_type: 'Stock',
  exchange: 'NSE',
};

const mockTransactions: Transaction[] = [
  {
    id: 'tx-1',
    asset_id: 'asset-1',
    portfolio_id: 'portfolio-1',
    transaction_type: 'BUY',
    quantity: 100,
    price_per_unit: 150,
    fees: 10,
    transaction_date: '2023-01-15T10:00:00Z',
    created_at: '2023-01-15T10:00:00Z',
    updated_at: '2023-01-15T10:00:00Z',
  },
];

const queryClient = new QueryClient();

const renderComponent = (onClose = jest.fn(), onEdit = jest.fn(), onDelete = jest.fn()) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <HoldingDetailModal
        holding={mockHolding}
        portfolioId="portfolio-1"
        onClose={onClose}
        onEditTransaction={onEdit}
        onDeleteTransaction={onDelete}
      />
    </QueryClientProvider>
  );
};

describe('HoldingDetailModal', () => {
  beforeEach(() => {
    jest.spyOn(portfolioHooks, 'useAssetTransactions').mockReturnValue({
      data: mockTransactions,
      isLoading: false,
      error: null,
    } as any);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders holding details and transaction list correctly', () => {
    jest.spyOn(portfolioHooks, 'useAssetAnalytics').mockReturnValue({
      data: { realized_xirr: 0.1234, unrealized_xirr: 0.2345 },
      isLoading: false,
      isError: false,
    } as any);

    renderComponent();

    expect(screen.getByText('Test Asset (TEST)')).toBeInTheDocument();

    // Helper function to find a summary value by its label, making the query robust and unambiguous.
    const getSummaryValueByLabel = (label: string): HTMLElement => {
      // Find the <p> tag that is the label to disambiguate from table headers.
      const labelElement = screen.getAllByText(label).find(el => el.tagName.toLowerCase() === 'p');
      if (!labelElement) throw new Error(`Could not find summary label: ${label}`);
      const container = labelElement.parentElement!;
      return container;
    };

    expect(within(getSummaryValueByLabel('Quantity')).getByText('100')).toBeInTheDocument();
    expect(within(getSummaryValueByLabel('Avg. Buy Price')).getByText('₹150.00')).toBeInTheDocument();
    expect(within(getSummaryValueByLabel('Current Value')).getByText('₹16,000.00')).toBeInTheDocument();
    expect(within(getSummaryValueByLabel('Unrealized P&L')).getByText('₹1,000.00')).toBeInTheDocument();


    // Check for analytics data
    expect(screen.getByText('12.34%')).toBeInTheDocument();
    expect(screen.getByText('23.45%')).toBeInTheDocument();

    // Check for transaction row
    const table = screen.getByRole('table');
    expect(within(table).getByText('15 Jan 2023')).toBeInTheDocument();
  });

  it('displays loading state for analytics', () => {
    jest.spyOn(portfolioHooks, 'useAssetAnalytics').mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as any);

    renderComponent();

    expect(screen.getByText('Realized XIRR')).toBeInTheDocument();
    expect(screen.getByText('Unrealized XIRR')).toBeInTheDocument();
    const loadingElements = screen.getAllByText('...');
    expect(loadingElements).toHaveLength(2);
  });

  it('displays error state for analytics', () => {
    jest.spyOn(portfolioHooks, 'useAssetAnalytics').mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as any);

    renderComponent();

    expect(screen.getByText('Realized XIRR')).toBeInTheDocument();
    expect(screen.getByText('Unrealized XIRR')).toBeInTheDocument();
    const errorElements = screen.getAllByText('N/A');
    expect(errorElements).toHaveLength(2);
  });
});


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
  total_invested_amount: 15000,
  current_price: 160,
  current_value: 16000,
  days_pnl: 100,
  days_pnl_percentage: 0.00625,
  unrealized_pnl: 1000,
  unrealized_pnl_percentage: 0.0666,
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
    asset: {
        id: 'asset-1',
        name: 'Test Asset',
        ticker_symbol: 'TEST',
        asset_type: 'Stock',
        currency: 'INR',
        isin: 'US0378331005',
        exchange: 'NASDAQ',
    }
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

    expect(within(screen.getByTestId('summary-quantity')).getByText('100')).toBeInTheDocument();
    expect(within(screen.getByTestId('summary-avg-buy-price')).getByText('₹150.00')).toBeInTheDocument();
    expect(within(screen.getByTestId('summary-current-value')).getByText('₹16,000.00')).toBeInTheDocument();
    expect(within(screen.getByTestId('summary-unrealized-pnl')).getByText('₹1,000.00')).toBeInTheDocument();

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


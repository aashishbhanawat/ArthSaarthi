import { render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider, UseQueryResult } from '@tanstack/react-query';
import HoldingDetailModal from '../../../components/Portfolio/HoldingDetailModal';
import * as portfolioHooks from '../../../hooks/usePortfolios';
import { Holding } from '../../../types/holding';
import { Transaction } from '../../../types/portfolio';
import { Asset } from '../../../types/asset';

const mockHolding: Holding = {
  asset_id: 'asset-1',
  asset_name: 'Test Asset',
  ticker_symbol: 'TEST',
  asset_type: 'Stock',
  exchange: 'NSE',
  quantity: 100,
  average_buy_price: 150,
  current_price: 160,
  current_value: 16000,
  unrealized_pnl: 1000,
  total_invested_amount: 15000,
  days_pnl: 100,
  days_pnl_percentage: 1,
  unrealized_pnl_percentage: 10,
};

const mockAsset: Asset = {
    id: 'asset-1',
    ticker_symbol: 'TEST',
    name: 'Test Asset',
    asset_type: 'Stock',
    currency: 'USD',
    exchange: 'NSE',
    isin: 'US0378331005'
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
    asset: mockAsset,
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

const createMockQueryResult = <TData,>(data: TData, options: Partial<UseQueryResult<TData, Error>> = {}): UseQueryResult<TData, Error> => {
    const defaults: UseQueryResult<TData, Error> = {
        data,
        error: null,
        isError: false,
        isLoading: false,
        isSuccess: true,
        status: 'success',
        refetch: jest.fn(),
        isInitialLoading: false,
        isStale: false,
        isRefetching: false,
        isPlaceholderData: false,
        isFetching: false,
        isFetchedAfterMount: true,
        isFetched: true,
        fetchStatus: 'idle'
    };
    return { ...defaults, ...options } as UseQueryResult<TData, Error>;
};

describe('HoldingDetailModal', () => {
  beforeEach(() => {
    jest.spyOn(portfolioHooks, 'useAssetTransactions').mockReturnValue(
        createMockQueryResult(mockTransactions)
    );
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders holding details and transaction list correctly', () => {
    jest.spyOn(portfolioHooks, 'useAssetAnalytics').mockReturnValue(
        createMockQueryResult({ realized_xirr: 0.1234, unrealized_xirr: 0.2345, sharpe_ratio: 1.23 })
    );

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
    jest.spyOn(portfolioHooks, 'useAssetAnalytics').mockReturnValue(
        createMockQueryResult(undefined, { isLoading: true })
    );

    renderComponent();

    expect(screen.getByText('Realized XIRR')).toBeInTheDocument();
    expect(screen.getByText('Unrealized XIRR')).toBeInTheDocument();
    const loadingElements = screen.getAllByText('...');
    expect(loadingElements).toHaveLength(2);
  });

  it('displays error state for analytics', () => {
    jest.spyOn(portfolioHooks, 'useAssetAnalytics').mockReturnValue(
        createMockQueryResult(undefined, { isError: true })
    );

    renderComponent();

    expect(screen.getByText('Realized XIRR')).toBeInTheDocument();
    expect(screen.getByText('Unrealized XIRR')).toBeInTheDocument();
    const errorElements = screen.getAllByText('N/A');
    expect(errorElements).toHaveLength(2);
  });
});

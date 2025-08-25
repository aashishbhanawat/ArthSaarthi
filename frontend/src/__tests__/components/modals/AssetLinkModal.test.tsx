import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import AssetLinkModal from '../../../components/modals/AssetLinkModal';
import * as usePortfolios from '../../../hooks/usePortfolios';
import * as useGoals from '../../../hooks/useGoals';
import { Portfolio } from '../../../types/portfolio';
import { Asset } from '../../../types/asset';
import { GoalLinkCreateIn, GoalLink } from '../../../types/goal';

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockPortfolios: Portfolio[] = [
  { id: 'p1', name: 'Portfolio 1', description: '', user_id: '1', transactions: [] },
];

const mockAssets: Asset[] = [
  { id: 'a1', name: 'Apple', ticker_symbol: 'AAPL', asset_type: 'stock', currency: 'USD', exchange: 'NASDAQ' },
];

describe('AssetLinkModal', () => {
  beforeEach(() => {
    jest.spyOn(usePortfolios, 'usePortfolios').mockReturnValue({
      data: mockPortfolios,
      isLoading: false,
    } as UseQueryResult<Portfolio[], Error>);

    jest.spyOn(usePortfolios, 'usePortfolioAssets').mockReturnValue({
      data: mockAssets,
      isLoading: false,
    } as UseQueryResult<Asset[], Error>);

    jest.spyOn(useGoals, 'useCreateGoalLink').mockReturnValue({
      mutate: jest.fn(),
    } as unknown as UseMutationResult<GoalLink, Error, { goalId: string; data: GoalLinkCreateIn }, unknown>);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders correctly and allows switching between portfolio and asset selection', () => {
    render(<AssetLinkModal isOpen={true} onClose={() => {}} goalId="g1" />, { wrapper });

    expect(screen.getByText('Link Asset or Portfolio to Goal')).toBeInTheDocument();

    // Default to portfolio view
    expect(screen.getByText('Portfolio 1')).toBeInTheDocument();

    // Switch to asset view
    fireEvent.click(screen.getByText('Assets'));
    expect(screen.getByText('Select a Portfolio to view its Assets')).toBeInTheDocument();
  });
});

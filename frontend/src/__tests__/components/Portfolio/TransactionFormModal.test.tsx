// This is a test comment
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import TransactionFormModal from '../../../components/Portfolio/TransactionFormModal';
import * as assetHooks from '../../../hooks/useAssets';
import { Transaction } from '../../../types/portfolio';
import { Asset, MutualFundSearchResult } from '../../../types/asset';

// Mocks
const mockCreateTransaction = jest.fn();
const mockUpdateTransaction = jest.fn();
const mockCreateAsset = jest.fn();
const mockLookupAsset = jest.fn();

jest.mock('../../../hooks/usePortfolios', () => ({
  useCreateTransaction: () => ({
    mutate: mockCreateTransaction,
  }),
  useUpdateTransaction: () => ({
    mutate: mockUpdateTransaction,
  }),
}));

jest.mock('../../../hooks/useAssets', () => ({
  useAssetSearch: jest.fn(),
  useCreateAsset: () => ({
    mutate: mockCreateAsset,
  }),
  useMfSearch: jest.fn(),
}));

jest.mock('../../../services/portfolioApi', () => ({
  // Use a function factory to avoid hoisting issues with mockLookupAsset
  lookupAsset: (...args: unknown[]) => mockLookupAsset(...args),
}));

const queryClient = new QueryClient();

const mockAssets: Asset[] = [
  { id: 'asset-1', ticker_symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'Stock', currency: 'USD', isin: null, exchange: 'NASDAQ' },
  { id: 'asset-2', ticker_symbol: 'GOOGL', name: 'Alphabet Inc.', asset_type: 'Stock', currency: 'USD', isin: null, exchange: 'NASDAQ' },
];

const mockMfSearchResults: MutualFundSearchResult[] = [
  {
    ticker_symbol: '120503',
    name: 'HDFC Index Fund - S&P BSE Sensex Plan',
    asset_type: 'Mutual Fund',
  },
];

const mockTransaction: Transaction = {
  id: 'tx-1',
  portfolio_id: 'portfolio-1',
  asset_id: 'asset-1',
  asset: mockAssets[0],
  transaction_type: 'BUY',
  quantity: '10',
  price_per_unit: '150.00',
  fees: '5.00',
  transaction_date: new Date().toISOString(),
};

const mockOnClose = jest.fn();

const renderComponent = (transactionToEdit: Transaction | null = null) => {
  (assetHooks.useAssetSearch as jest.Mock).mockReturnValue({
    data: mockAssets,
    isLoading: false,
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <TransactionFormModal
          isOpen={true}
          onClose={mockOnClose}
          portfolioId="portfolio-1"
          transactionToEdit={transactionToEdit}
        />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('TransactionFormModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockLookupAsset.mockResolvedValue(mockAssets);
    (assetHooks.useMfSearch as jest.Mock).mockReturnValue({
      data: mockMfSearchResults,
      isLoading: false,
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Create Mode', () => {
    it('renders the "Add Transaction" title and form', () => {
      renderComponent();
      expect(screen.getByRole('heading', { name: /add transaction/i })).toBeInTheDocument();
      expect(screen.getByLabelText('Asset', { selector: 'input' })).not.toBeDisabled();
    });

    it('searches for and selects an asset', async () => {
        renderComponent();
        const assetInput = screen.getByLabelText('Asset', { selector: 'input' });
        fireEvent.change(assetInput, { target: { value: 'Apple' } });
        
        await waitFor(() => {
            expect(mockLookupAsset).toHaveBeenCalledWith('Apple');
        });
        
        fireEvent.click(await screen.findByText('Apple Inc. (AAPL)'));
        expect(assetInput).toHaveValue('Apple Inc.');
    });

    it('submits the form and calls createTransaction mutation', async () => {
      renderComponent();
      // Select an asset first
      const assetInput = screen.getByLabelText('Asset', { selector: 'input' });
      fireEvent.change(assetInput, { target: { value: 'Apple' } }); // This will trigger the search
      fireEvent.click(await screen.findByText('Apple Inc. (AAPL)'));

      // Fill other fields
      fireEvent.change(screen.getByLabelText(/quantity/i), { target: { value: '10' } });
      fireEvent.change(screen.getByLabelText(/price per unit/i), { target: { value: '150' } });
      fireEvent.change(screen.getByLabelText(/date/i), { target: { value: '2023-01-01' } });

      fireEvent.click(screen.getByRole('button', { name: /save transaction/i }));

      await waitFor(() => {
        expect(mockCreateTransaction).toHaveBeenCalledWith(
          expect.objectContaining({
            data: expect.objectContaining({
              asset_id: 'asset-1',
              quantity: 10,
              price_per_unit: 150,
            }),
          }), expect.any(Object));
      });
    });

    it('searches for and creates a mutual fund transaction', async () => {
      renderComponent();

      // Switch to Mutual Fund
      const assetTypeSelect = screen.getByLabelText(/asset type/i);
      fireEvent.change(assetTypeSelect, { target: { value: 'Mutual Fund' } });

      const mfSearchInput = screen.getByLabelText('Asset');
      fireEvent.focus(mfSearchInput);
      fireEvent.change(mfSearchInput, { target: { value: 'hdfc' } });

      // Wait for the debounced hook to be called
      await waitFor(() => {
        expect(assetHooks.useMfSearch).toHaveBeenCalledWith('hdfc');
      });

      // Select the MF from the dropdown
      fireEvent.click(await screen.findByText('HDFC Index Fund - S&P BSE Sensex Plan'));

      // Fill other fields
      fireEvent.change(screen.getByLabelText(/quantity/i), { target: { value: '50' } });
      fireEvent.change(screen.getByLabelText(/price per unit/i), { target: { value: '250' } });
      fireEvent.change(screen.getByLabelText(/date/i), { target: { value: '2023-02-01' } });

      // Submit the form
      fireEvent.click(screen.getByRole('button', { name: /save transaction/i }));

      // Assert the mutation was called with the correct payload
      await waitFor(() => {
        expect(mockCreateTransaction).toHaveBeenCalledWith(
          expect.objectContaining({
            data: expect.objectContaining({
              ticker_symbol: '120503',
              asset_type: 'Mutual Fund',
              quantity: 50,
              price_per_unit: 250,
            }),
          }),
          expect.any(Object)
        );
      });
    });
  });

  describe('Edit Mode', () => {
    it('renders the "Edit Transaction" title and pre-populates form', () => {
      renderComponent(mockTransaction);
      expect(screen.getByRole('heading', { name: /edit transaction/i })).toBeInTheDocument();
      expect(screen.getByLabelText('Asset', { selector: 'input' })).toBeDisabled();
      expect(screen.getByLabelText('Asset', { selector: 'input' })).toHaveValue('Apple Inc.');
      expect(screen.getByLabelText(/quantity/i)).toHaveValue(10);
      expect(screen.getByLabelText(/price per unit/i)).toHaveValue(150);
    });

    it('submits the form and calls updateTransaction mutation', async () => {
      renderComponent(mockTransaction);

      fireEvent.change(screen.getByLabelText(/quantity/i), { target: { value: '20' } });

      fireEvent.click(screen.getByRole('button', { name: /save changes/i }));

      await waitFor(() => {
        expect(mockUpdateTransaction).toHaveBeenCalledWith({
          portfolioId: 'portfolio-1',
          transactionId: 'tx-1',
          data: expect.objectContaining({
            quantity: 20,
          }),
        }, expect.any(Object));
      });
    });
  });

  it('displays an API error on failure', async () => {
    const errorMessage = 'Network Error';
    mockCreateTransaction.mockImplementation((_payload, options) => {
      options?.onError?.(new Error(errorMessage));
    });
    renderComponent();
    
    // Select an asset
    const assetInput = screen.getByLabelText('Asset', { selector: 'input' });
    fireEvent.change(assetInput, { target: { value: 'Apple' } });
    fireEvent.click(await screen.findByText('Apple Inc. (AAPL)'));

    // Fill other fields
    fireEvent.change(screen.getByLabelText(/quantity/i), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText(/price per unit/i), { target: { value: '150' } });
    fireEvent.change(screen.getByLabelText(/date/i), { target: { value: '2023-01-01' } });

    fireEvent.click(screen.getByRole('button', { name: /save transaction/i }));

    expect(await screen.findByText(/network error/i)).toBeInTheDocument();
  });
});
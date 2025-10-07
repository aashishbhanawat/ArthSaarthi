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
const mockLookupAsset = jest.fn();
const mockCreateFixedDeposit = jest.fn();
const mockCreatePpfAccount = jest.fn();
const mockCreateBond = jest.fn();

jest.mock('../../../hooks/usePortfolios', () => ({
  useCreateTransaction: () => ({
    mutate: mockCreateTransaction,
  }),
  useUpdateTransaction: () => ({
    mutate: mockUpdateTransaction,
  }),
  useCreateFixedDeposit: () => ({
    mutate: mockCreateFixedDeposit,
  }),
  useCreatePpfAccount: () => ({
    mutate: mockCreatePpfAccount,
  }),
  useCreateBond: () => ({
    mutate: mockCreateBond,
  }),
}));

// Mock the entire module
jest.mock('../../../hooks/useAssets', () => ({
  ...jest.requireActual('../../../hooks/useAssets'), // import and retain default behavior
  useAssetsByType: jest.fn(), // mock useAssetsByType
  useAssetSearch: jest.fn(),
  useMfSearch: jest.fn(),
}));


jest.mock('../../../services/portfolioApi', () => ({
  // Use a function factory to avoid hoisting issues with mockLookupAsset
  lookupAsset: (...args: unknown[]) => mockLookupAsset(...args),
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false, // Prevent retries in tests
    },
  },
});

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
    // Default mock for useAssetsByType
    (assetHooks.useAssetsByType as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
    });
    mockLookupAsset.mockResolvedValue(mockAssets);
    (assetHooks.useMfSearch as jest.Mock).mockReturnValue({
      data: mockMfSearchResults,
      isLoading: false,
    });
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
            expect(mockLookupAsset).toHaveBeenCalledWith('Apple', 'STOCK');
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

      fireEvent.click(screen.getByRole('button', { name: /save/i }));

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
      fireEvent.click(screen.getByRole('button', { name: /save/i }));

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

    it('submits the form and calls createPpfAccount mutation for a new PPF account', async () => {
      // Ensure the hook returns no existing PPF accounts
      (assetHooks.useAssetsByType as jest.Mock).mockReturnValue({ data: [], isLoading: false });
      renderComponent();

      // Switch to PPF Account
      const assetTypeSelect = screen.getByLabelText(/asset type/i);
      fireEvent.change(assetTypeSelect, { target: { value: 'PPF Account' } });

      // Wait for the UI to update and show the creation form
      expect(await screen.findByText(/create your ppf account/i)).toBeInTheDocument();

      // Fill PPF fields
      fireEvent.change(screen.getByLabelText(/institution name/i), { target: { value: 'Test PPF Bank' } });
      fireEvent.change(screen.getByLabelText(/account number/i), { target: { value: 'PPF123' } });
      fireEvent.change(screen.getByLabelText(/opening date/i), { target: { value: '2023-01-01' } });
      fireEvent.change(screen.getByLabelText(/contribution amount/i), { target: { value: '50000' } });
      fireEvent.change(screen.getByLabelText(/contribution date/i), { target: { value: '2023-01-15' } });

      // Submit the form
      fireEvent.click(screen.getByRole('button', { name: /save/i }));

      // Assert the mutation was called with the correct payload
      await waitFor(() => {
        expect(mockCreatePpfAccount).toHaveBeenCalledWith(
          {
            portfolioId: 'portfolio-1',
            data: {
              institution_name: 'Test PPF Bank',
              account_number: 'PPF123',
              opening_date: '2023-01-01',
              amount: 50000,
              contribution_date: '2023-01-15',
            },
          },
          expect.any(Object)
        );
      });
    });

    it('submits the form and calls createTransaction for an existing PPF account', async () => {
      const mockPpfAsset = { id: 'ppf-asset-1', name: 'Existing PPF', asset_type: 'PPF', account_number: '123' };
      (assetHooks.useAssetsByType as jest.Mock).mockReturnValue({ data: [mockPpfAsset], isLoading: false });

      renderComponent();

      // Switch to PPF Account
      const assetTypeSelect = screen.getByLabelText(/asset type/i);
      fireEvent.change(assetTypeSelect, { target: { value: 'PPF Account' } });

      // Wait for the UI to update and show the contribution form
      expect(await screen.findByText(/existing ppf account/i)).toBeInTheDocument();

      // Fill contribution fields
      fireEvent.change(screen.getByLabelText(/contribution amount/i), { target: { value: '10000' } });
      fireEvent.change(screen.getByLabelText(/contribution date/i), { target: { value: '2024-05-10' } });

      // Submit the form
      fireEvent.click(screen.getByRole('button', { name: /save/i }));

      // Assert the mutation was called with the correct payload
      await waitFor(() => {
        expect(mockCreateTransaction).toHaveBeenCalledWith(
          expect.objectContaining({
            portfolioId: 'portfolio-1',
            data: {
              asset_id: 'ppf-asset-1',
              asset_type: 'PPF',
              transaction_type: 'CONTRIBUTION',
              quantity: 10000,
              price_per_unit: 1,
              transaction_date: new Date('2024-05-10T00:00:00.000Z').toISOString(),
            },
          }),
          expect.any(Object)
        );
      });
    });

    it('submits the form and calls createFixedDeposit mutation', async () => {
      renderComponent();

      // Switch to Fixed Deposit
      const assetTypeSelect = screen.getByLabelText(/asset type/i);
      fireEvent.change(assetTypeSelect, { target: { value: 'Fixed Deposit' } });

      // Fill FD fields
      fireEvent.change(screen.getByLabelText(/institution name/i), { target: { value: 'Test Bank' } });
      fireEvent.change(screen.getByLabelText(/fd account number/i), { target: { value: 'FD12345' } });
      fireEvent.change(screen.getByLabelText(/principal amount/i), { target: { value: '100000' } });
      fireEvent.change(screen.getByLabelText(/interest rate/i), { target: { value: '6.5' } });
      fireEvent.change(screen.getByLabelText(/start date/i), { target: { value: '2023-01-01' } });
      fireEvent.change(screen.getByLabelText(/maturity date/i), { target: { value: '2025-01-01' } });

      // Submit the form
      fireEvent.click(screen.getByRole('button', { name: /save/i }));

      // Assert the mutation was called with the correct payload
      await waitFor(() => {
        expect(mockCreateFixedDeposit).toHaveBeenCalledWith(
          {
            portfolioId: 'portfolio-1',
            data: {
              name: 'Test Bank',
              account_number: 'FD12345',
              principal_amount: 100000,
              interest_rate: 6.5,
              start_date: '2023-01-01',
              maturity_date: '2025-01-01',
              compounding_frequency: 'Annually',
              interest_payout: 'Cumulative'
            },
          },
          expect.any(Object)
        );
      });
    });
  });

  describe('Corporate Actions', () => {
    it('renders the Dividend form and submits correctly', async () => {
        renderComponent();
        // Select a stock asset first, as corporate actions are stock-only
        const assetInput = screen.getByLabelText('Asset', { selector: 'input' });
        fireEvent.change(assetInput, { target: { value: 'Apple' } });
        fireEvent.click(await screen.findByText('Apple Inc. (AAPL)'));
        // Select 'Corporate Action' transaction type
        const transactionTypeSelect = screen.getByLabelText('Transaction Type');
        fireEvent.change(transactionTypeSelect, { target: { value: 'Corporate Action' } });

        // The action type should default to DIVIDEND
        expect(screen.getByLabelText('Action Type')).toHaveValue('DIVIDEND');

        // Check for dividend-specific fields
        expect(screen.getByLabelText('Payment Date')).toBeInTheDocument();
        expect(screen.getByLabelText('Total Amount')).toBeInTheDocument();
        expect(screen.getByLabelText('Reinvest this dividend?')).toBeInTheDocument();

        // Fill form
        fireEvent.change(screen.getByLabelText('Payment Date'), { target: { value: '2024-07-15' } });
        fireEvent.change(screen.getByLabelText('Total Amount'), { target: { value: '1500' } });
        fireEvent.click(screen.getByLabelText('Reinvest this dividend?'));

        // Submit
        fireEvent.click(screen.getByRole('button', { name: /save/i }));

        await waitFor(() => {
            expect(mockCreateTransaction).toHaveBeenCalledWith(
                expect.objectContaining({
                    data: {
                        asset_id: 'asset-1',
                        transaction_type: 'DIVIDEND',
                        quantity: 1500, // Repurposed for cash amount
                        price_per_unit: 1,
                        transaction_date: new Date('2024-07-15T00:00:00.000Z').toISOString(),
                        is_reinvested: true,
                    },
                }),
                expect.any(Object)
            );
        });
    });

    it('renders the Stock Split form and submits correctly', async () => {
        renderComponent();
        // Select a stock asset first, as corporate actions are stock-only
        const assetInput = screen.getByLabelText('Asset', { selector: 'input' });
        fireEvent.change(assetInput, { target: { value: 'Apple' } });
        fireEvent.click(await screen.findByText('Apple Inc. (AAPL)'));
        // Select 'Corporate Action' transaction type
        const transactionTypeSelect = screen.getByLabelText('Transaction Type');
        fireEvent.change(transactionTypeSelect, { target: { value: 'Corporate Action' } });

        const actionTypeSelect = screen.getByLabelText('Action Type');
        fireEvent.change(actionTypeSelect, { target: { value: 'SPLIT' } });

        expect(await screen.findByText('Split Ratio')).toBeInTheDocument();

        // Fill form
        fireEvent.change(screen.getByLabelText('Effective Date'), { target: { value: '2024-08-01' } });
        fireEvent.change(screen.getByRole('spinbutton', { name: 'New shares' }), { target: { value: '3' } });
        fireEvent.change(screen.getByRole('spinbutton', { name: 'Old shares' }), { target: { value: '1' } });

        // Submit
        fireEvent.click(screen.getByRole('button', { name: /save/i }));

        await waitFor(() => {
            expect(mockCreateTransaction).toHaveBeenCalledWith(
                expect.objectContaining({
                    data: {
                        asset_id: 'asset-1',
                        transaction_type: 'SPLIT',
                        quantity: 3, // Repurposed for new ratio
                        price_per_unit: 1, // Repurposed for old ratio
                        transaction_date: new Date('2024-08-01T00:00:00.000Z').toISOString(),
                    },
                }),
                expect.any(Object)
            );
        });
    });

    it('renders the Bonus Issue form and submits correctly', async () => {
        renderComponent();
        // Select a stock asset first, as corporate actions are stock-only
        const assetInput = screen.getByLabelText('Asset', { selector: 'input' });
        fireEvent.change(assetInput, { target: { value: 'Apple' } });
        fireEvent.click(await screen.findByText('Apple Inc. (AAPL)'));
        // Select 'Corporate Action' transaction type
        const transactionTypeSelect = screen.getByLabelText('Transaction Type');
        fireEvent.change(transactionTypeSelect, { target: { value: 'Corporate Action' } });

        const actionTypeSelect = screen.getByLabelText('Action Type');
        fireEvent.change(actionTypeSelect, { target: { value: 'BONUS' } });

        expect(await screen.findByText('Bonus Ratio')).toBeInTheDocument();

        // Fill form
        fireEvent.change(screen.getByLabelText('Effective Date'), { target: { value: '2024-09-10' } });
        fireEvent.change(screen.getByRole('spinbutton', { name: 'New bonus shares' }), { target: { value: '1' } });
        fireEvent.change(screen.getByRole('spinbutton', { name: 'Old held shares' }), { target: { value: '5' } });

        // Submit
        fireEvent.click(screen.getByRole('button', { name: /save/i }));

        await waitFor(() => {
            expect(mockCreateTransaction).toHaveBeenCalledWith(
                expect.objectContaining({
                    data: {
                        asset_id: 'asset-1',
                        transaction_type: 'BONUS',
                        quantity: 1, // Repurposed for new shares
                        price_per_unit: 5, // Repurposed for old shares
                        transaction_date: new Date('2024-09-10T00:00:00.000Z').toISOString(),
                    },
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
            quantity: 20, // The updated value
            price_per_unit: 150, // Should remain the same
            fees: 5, // Should remain the same
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

    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    expect(await screen.findByText(/network error/i)).toBeInTheDocument();
  });
});
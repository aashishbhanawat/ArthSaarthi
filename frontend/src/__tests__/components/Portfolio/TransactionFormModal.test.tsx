import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TransactionFormModal from '../../../components/Portfolio/TransactionFormModal';
import * as portfolioHooks from '../../../hooks/usePortfolios';
import * as portfolioApi from '../../../services/portfolioApi';
import { Transaction } from '../../../types/portfolio';
import { Asset } from '../../../types/asset';

// Mock hooks and services
jest.mock('../../../hooks/usePortfolios');
jest.mock('../../../services/portfolioApi');

const mockUseCreateTransaction = portfolioHooks.useCreateTransaction as jest.Mock;
const mockUseUpdateTransaction = portfolioHooks.useUpdateTransaction as jest.Mock;
const mockUseCreateAsset = portfolioHooks.useCreateAsset as jest.Mock;
const mockLookupAsset = portfolioApi.lookupAsset as jest.Mock;

const queryClient = new QueryClient();

const mockAsset: Asset = {
  id: 'asset-1',
  ticker_symbol: 'TEST',
  name: 'Test Asset Inc.',
  asset_type: 'Stock',
  currency: 'USD',
  isin: 'US0378331005',
  exchange: 'NASDAQ',
};

const mockTransaction: Transaction = {
  id: 'tx-123',
  asset_id: 'asset-1',
  portfolio_id: 'p-1',
  transaction_type: 'BUY',
  quantity: 10,
  price_per_unit: 150,
  fees: 5,
  transaction_date: '2023-10-26T10:00:00Z',
  asset: mockAsset,
};

describe('TransactionFormModal', () => {
  let createTransactionMutate: jest.Mock;
  let updateTransactionMutate: jest.Mock;
  let createAssetMutate: jest.Mock;
  const mockOnClose = jest.fn();

  beforeEach(() => {
    createTransactionMutate = jest.fn();
    updateTransactionMutate = jest.fn();
    createAssetMutate = jest.fn();

    mockUseCreateTransaction.mockReturnValue({ mutate: createTransactionMutate, isPending: false });
    mockUseUpdateTransaction.mockReturnValue({ mutate: updateTransactionMutate, isPending: false });
    mockUseCreateAsset.mockReturnValue({ mutate: createAssetMutate, isPending: false });
    mockLookupAsset.mockResolvedValue([mockAsset]);
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  const renderComponent = (transactionToEdit?: Transaction) => {
    render(
      <QueryClientProvider client={queryClient}>
        <TransactionFormModal
          portfolioId="p-1"
          onClose={mockOnClose}
          transactionToEdit={transactionToEdit}
        />
      </QueryClientProvider>
    );
  };

  describe('Create Mode', () => {
    it('renders the "Add Transaction" title and form', () => {
      renderComponent();
      expect(screen.getByRole('heading', { name: /add transaction/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/asset/i)).not.toBeDisabled();
    });

    it('searches for and selects an asset', async () => {
      renderComponent();
      const assetInput = screen.getByLabelText(/asset/i);
      fireEvent.change(assetInput, { target: { value: 'Test' } });
      act(() => {
        jest.runAllTimers();
      });

      expect(await screen.findByText(/test asset inc./i)).toBeInTheDocument();
      fireEvent.click(screen.getByText(/test asset inc./i));

      expect(assetInput).toHaveValue('Test Asset Inc.');
    });

    it('allows creating a new asset if not found', async () => {
      mockLookupAsset.mockResolvedValue([]);
      renderComponent();
      const assetInput = screen.getByLabelText(/asset/i);
      fireEvent.change(assetInput, { target: { value: 'NEW' } });

      act(() => {
        jest.runAllTimers();
      });

      expect(await screen.findByRole('button', { name: /create asset "NEW"/i })).toBeInTheDocument();
      fireEvent.click(screen.getByRole('button', { name: /create asset "NEW"/i }));

      expect(createAssetMutate).toHaveBeenCalledWith('NEW', expect.any(Object));
    });

    it('submits the form and calls createTransaction mutation', async () => {
      renderComponent();
      // Select an asset first
      const assetInput = screen.getByLabelText(/asset/i);
      fireEvent.change(assetInput, { target: { value: 'Test' } });
      act(() => {
        jest.runAllTimers();
      });
      const searchResult = await screen.findByText(/test asset inc./i);
      fireEvent.click(searchResult);

      // Fill the rest of the form
      fireEvent.change(screen.getByLabelText(/type/i), { target: { value: 'BUY' } });
      fireEvent.change(screen.getByLabelText(/quantity/i), { target: { value: '10' } });
      fireEvent.change(screen.getByLabelText(/price per unit/i), { target: { value: '100' } });
      fireEvent.change(screen.getByLabelText(/date/i), { target: { value: '2023-01-01' } });

      fireEvent.click(screen.getByRole('button', { name: /save transaction/i }));

      await waitFor(() => {
        expect(createTransactionMutate).toHaveBeenCalledWith(
          expect.objectContaining({
            portfolioId: 'p-1',
            data: expect.objectContaining({
              asset_id: 'asset-1',
              quantity: 10,
              price_per_unit: 100,
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
      expect(screen.getByLabelText(/asset/i)).toBeDisabled();
      expect(screen.getByLabelText(/asset/i)).toHaveValue('Test Asset Inc.');
      expect(screen.getByLabelText(/quantity/i)).toHaveValue(10);
      expect(screen.getByLabelText(/price per unit/i)).toHaveValue(150);
    });

    it('submits the form and calls updateTransaction mutation', async () => {
      renderComponent(mockTransaction);

      // Use fireEvent for simple input changes to avoid conflicts with fake timers
      fireEvent.change(screen.getByLabelText(/quantity/i), { target: { value: '20' } });

      fireEvent.click(screen.getByRole('button', { name: /save changes/i }));

      await waitFor(() => {
        expect(updateTransactionMutate).toHaveBeenCalledWith(
          expect.objectContaining({
            portfolioId: 'p-1',
            transactionId: 'tx-123',
            data: expect.objectContaining({
              quantity: 20,
              price_per_unit: 150, // Unchanged
            }),
          }),
          expect.any(Object)
        );
      });
    });
  });

  it('displays an API error on failure', async () => {
    const error = { response: { data: { detail: 'A test error occurred' } } };
    createTransactionMutate.mockImplementation((_payload, { onError }) => {
      onError(error);
    });

    renderComponent();
    // Select an asset
    fireEvent.change(screen.getByLabelText(/asset/i), { target: { value: 'Test' } });
    act(() => {
      jest.runAllTimers();
    });
    const searchResult = await screen.findByText(/test asset inc./i);
      fireEvent.click(searchResult);

    // Fill form to pass client-side validation
    fireEvent.change(screen.getByLabelText(/quantity/i), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText(/price per unit/i), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText(/date/i), { target: { value: '2023-01-01' } });

    // Submit
      fireEvent.click(screen.getByRole('button', { name: /save transaction/i }));

    await waitFor(() => {
      expect(screen.getByText('A test error occurred')).toBeInTheDocument();
    });
  });
});
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import AddTransactionModal from '../../../components/Portfolio/AddTransactionModal';

// Mocks
const mockCreateTransaction = jest.fn();
const mockCreateAsset = jest.fn();
const mockLookupAsset = jest.fn();

jest.mock('../../../hooks/usePortfolios', () => ({
  useCreateTransaction: () => ({
    mutate: mockCreateTransaction,
  }),
}));

jest.mock('../../../hooks/useAssets', () => ({
  useCreateAsset: () => ({
    mutate: mockCreateAsset,
  }),
}));

jest.mock('../../../services/portfolioApi', () => ({
  // Use a function factory to avoid hoisting issues with mockLookupAsset
  lookupAsset: (...args: unknown[]) => mockLookupAsset(...args),
}));

const queryClient = new QueryClient();

const mockAssets = [
  { id: 'asset-1', ticker_symbol: 'AAPL', name: 'Apple Inc.' },
  { id: 'asset-2', ticker_symbol: 'GOOGL', name: 'Alphabet Inc.' },
];

const mockOnClose = jest.fn();

const renderComponent = () => {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AddTransactionModal
          isOpen={true} // <-- THE FIX
          onClose={mockOnClose}
          portfolioId="portfolio-uuid-1"
        />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('AddTransactionModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    // Default mock for successful lookup
    mockLookupAsset.mockResolvedValue(mockAssets);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders the modal with all form fields', () => {
    renderComponent();
    expect(screen.getByText('Add Transaction')).toBeInTheDocument();
    expect(screen.getByLabelText('Asset')).toBeInTheDocument();
    expect(screen.getByLabelText('Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Quantity')).toBeInTheDocument();
    expect(screen.getByLabelText('Price per Unit')).toBeInTheDocument();
  });

  it('searches for assets when user types in the input', async () => {
    renderComponent();
    const assetInput = screen.getByLabelText('Asset');
    fireEvent.change(assetInput, { target: { value: 'AAPL' } });

    act(() => {
      jest.runAllTimers();
    });

    await waitFor(() => {
      expect(mockLookupAsset).toHaveBeenCalledWith('AAPL');
    });

    const searchResult = await screen.findByText('Apple Inc. (AAPL)');
    expect(searchResult).toBeInTheDocument();
  });

  it('allows selecting an asset from search results', async () => {
    renderComponent();
    const assetInput = screen.getByLabelText('Asset');
    fireEvent.change(assetInput, { target: { value: 'GOOG' } });

    act(() => {
      jest.runAllTimers();
    });

    const searchResult = await screen.findByText('Alphabet Inc. (GOOGL)');
    fireEvent.click(searchResult);

    expect(assetInput).toHaveValue('Alphabet Inc. (GOOGL)');
  });

  it('submits the form with correct data for an existing asset', async () => {
    renderComponent();

    // Select an asset
    const assetInput = screen.getByLabelText('Asset');
    fireEvent.change(assetInput, { target: { value: 'AAPL' } });
    act(() => { jest.runAllTimers(); });
    const searchResult = await screen.findByText('Apple Inc. (AAPL)');
    fireEvent.click(searchResult);

    // Fill form
    fireEvent.change(screen.getByLabelText('Quantity'), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText('Price per Unit'), { target: { value: '150' } });
    fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2023-01-01' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Transaction' }));

    await waitFor(() => {
      expect(mockCreateTransaction).toHaveBeenCalledWith(
        {
          portfolioId: 'portfolio-uuid-1',
          data: expect.objectContaining({
            asset_id: 'asset-1',
            quantity: 10,
            price_per_unit: 150,
            transaction_date: new Date('2023-01-01').toISOString(),
          }),
        }, expect.any(Object));
    });
  });

  it('shows a "Create Asset" button when search returns no results', async () => {
    mockLookupAsset.mockResolvedValue([]);
    renderComponent();

    const assetInput = screen.getByLabelText('Asset');
    fireEvent.change(assetInput, { target: { value: 'NEW' } });

    act(() => {
      jest.runAllTimers();
    });

    const createButton = await screen.findByRole('button', {
      name: /create asset "new"/i,
    });
    expect(createButton).toBeInTheDocument();
  });

  it('calls the create asset mutation when the "Create Asset" button is clicked', async () => {
    mockLookupAsset.mockResolvedValue([]);
    mockCreateAsset.mockResolvedValue({ id: 'new-asset-id', name: 'New Asset', ticker_symbol: 'NEW' });
    renderComponent();

    const assetInput = screen.getByLabelText('Asset');
    fireEvent.change(assetInput, { target: { value: 'NEW' } });

    act(() => { jest.runAllTimers(); });

    const createButton = await screen.findByRole('button', {
      name: /create asset "new"/i,
    });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(mockCreateAsset).toHaveBeenCalledWith({ ticker: 'NEW' }, expect.any(Object));
    });
  });
});
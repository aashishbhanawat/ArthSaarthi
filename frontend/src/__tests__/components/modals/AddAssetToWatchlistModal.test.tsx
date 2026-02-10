import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AddAssetToWatchlistModal from '../../../components/modals/AddAssetToWatchlistModal';
import * as useAssetsHooks from '../../../hooks/useAssets';
import { lookupAsset } from '../../../services/portfolioApi';

jest.mock('../../../hooks/useAssets');
jest.mock('../../../hooks/useDebounce', () => ({
  __esModule: true,
  useDebounce: (value: unknown) => value,
}));
jest.mock('../../../services/portfolioApi', () => ({
  lookupAsset: jest.fn(),
  AssetSearchResult: jest.requireActual('../../../services/portfolioApi').AssetSearchResult,
}));

const mockUseAssetSearch = useAssetsHooks.useAssetSearch as jest.Mock;

const mockAssets = [
  { id: '1', ticker_symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'STOCK', currency: 'USD', exchange: 'NASDAQ' },
  { id: '2', ticker_symbol: 'GOOGL', name: 'Alphabet Inc.', asset_type: 'STOCK', currency: 'USD', exchange: 'NASDAQ' },
];

const queryClient = new QueryClient();

const renderComponent = (props: Partial<React.ComponentProps<typeof AddAssetToWatchlistModal>>) => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onAddAsset: jest.fn(),
  };
  return render(
    <QueryClientProvider client={queryClient}>
      <AddAssetToWatchlistModal {...defaultProps} {...props} />
    </QueryClientProvider>
  );
};

describe('AddAssetToWatchlistModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAssetSearch.mockReturnValue({ data: [], isLoading: false });
  });

  it('renders the modal and allows searching for an asset', async () => {
    mockUseAssetSearch.mockReturnValue({ data: mockAssets, isLoading: false });
    renderComponent({});

    const searchInput = screen.getByLabelText('Search for an asset');
    fireEvent.change(searchInput, { target: { value: 'AAPL' } });

    await waitFor(() => {
      expect(screen.getByText('Apple Inc. (AAPL)')).toBeInTheDocument();
    });
  });

  it('allows selecting a local asset and calls onAddAsset on submit', async () => {
    const onAddAsset = jest.fn();
    mockUseAssetSearch.mockReturnValue({ data: mockAssets, isLoading: false });
    renderComponent({ onAddAsset });

    const searchInput = screen.getByLabelText('Search for an asset');
    fireEvent.change(searchInput, { target: { value: 'GOOGL' } });

    const searchResult = await screen.findByText('Alphabet Inc. (GOOGL)');
    fireEvent.click(searchResult);

    const addButton = screen.getByRole('button', { name: 'Add Asset to Watchlist' });
    expect(addButton).not.toBeDisabled();
    fireEvent.click(addButton);

    expect(onAddAsset).toHaveBeenCalledWith('2');
  });

  it('creates and adds a foreign asset (missing ID) via lookupAsset', async () => {
    const onAddAsset = jest.fn();
    const foreignAsset = { ticker_symbol: 'MSFT', name: 'Microsoft', asset_type: 'STOCK', currency: 'USD' }; // No ID
    const createdAsset = { ...foreignAsset, id: 'new-id-123' };

    // Mock search returning a foreign asset (no ID)
    mockUseAssetSearch.mockReturnValue({ data: [foreignAsset], isLoading: false });
    // Mock lookup creating the asset
    (lookupAsset as jest.Mock).mockResolvedValue([createdAsset]);

    renderComponent({ onAddAsset });

    const searchInput = screen.getByLabelText('Search for an asset');
    fireEvent.change(searchInput, { target: { value: 'MSFT' } });

    const searchResult = await screen.findByText('Microsoft (MSFT)');
    fireEvent.click(searchResult);

    const addButton = screen.getByRole('button', { name: 'Add Asset to Watchlist' });
    fireEvent.click(addButton);

    // Should verify loading state or button change if possible, but mainly check calls
    expect(addButton).toBeDisabled(); // Should be disabled while adding

    await waitFor(() => {
      expect(lookupAsset).toHaveBeenCalledWith('MSFT', 'STOCK', true);
    });

    await waitFor(() => {
      expect(onAddAsset).toHaveBeenCalledWith('new-id-123');
    });
  });

  it('disables the add button when no asset is selected', () => {
    renderComponent({});
    const addButton = screen.getByRole('button', { name: 'Add Asset to Watchlist' });
    expect(addButton).toBeDisabled();
  });
});

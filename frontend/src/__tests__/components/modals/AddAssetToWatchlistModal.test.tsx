import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AddAssetToWatchlistModal from '../../../components/modals/AddAssetToWatchlistModal';
import * as useAssetsHooks from '../../../hooks/useAssets';
import { Asset } from '../../../types/asset';

jest.mock('../../../hooks/useAssets');

const mockUseAssetSearch = useAssetsHooks.useAssetSearch as jest.Mock;

const mockAssets: Asset[] = [
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

  it('allows selecting an asset and calls onAddAsset on submit', async () => {
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

  it('disables the add button when no asset is selected', () => {
    renderComponent({});
    const addButton = screen.getByRole('button', { name: 'Add Asset to Watchlist' });
    expect(addButton).toBeDisabled();
  });
});

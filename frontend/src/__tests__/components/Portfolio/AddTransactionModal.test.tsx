import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AddTransactionModal from '../../../components/Portfolio/AddTransactionModal';
import * as portfolioApi from '../../../services/portfolioApi';
import * as portfolioHooks from '../../../hooks/usePortfolios';
import { Asset } from '../../../types';

const mockLookupAsset = jest.spyOn(portfolioApi, 'lookupAsset');
const mockUseCreateTransaction = jest.spyOn(portfolioHooks, 'useCreateTransaction');
const mockUseCreateAsset = jest.spyOn(portfolioHooks, 'useCreateAsset');

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: false,
        },
    },
});

const mockOnClose = jest.fn();
const mockMutateTransaction = jest.fn();
const mockMutateAsset = jest.fn();

const mockAssets: Asset[] = [
    { id: 1, ticker_symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'Stock', currency: 'USD', exchange: 'NASDAQ' },
    { id: 2, ticker_symbol: 'GOOGL', name: 'Alphabet Inc.', asset_type: 'Stock', currency: 'USD', exchange: 'NASDAQ' },
];

const renderComponent = () => {
    return render(
        <QueryClientProvider client={queryClient}>
            <AddTransactionModal portfolioId={1} onClose={mockOnClose} />
        </QueryClientProvider>
    );
};

describe('AddTransactionModal', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // @ts-ignore
        mockUseCreateTransaction.mockReturnValue({ mutate: mockMutateTransaction, isPending: false });
        // @ts-ignore
        mockUseCreateAsset.mockReturnValue({ mutate: mockMutateAsset, isPending: false });
    });

    it('renders the modal with all form fields', () => {
        renderComponent();
        expect(screen.getByText('Add Transaction')).toBeInTheDocument();
        expect(screen.getByLabelText('Asset')).toBeInTheDocument();
        expect(screen.getByLabelText('Type')).toBeInTheDocument();
        expect(screen.getByLabelText('Quantity')).toBeInTheDocument();
        expect(screen.getByLabelText('Price per Unit')).toBeInTheDocument();
        expect(screen.getByLabelText('Date')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Save Transaction' })).toBeInTheDocument();
    });

    it('searches for assets when user types in the input', async () => {
        mockLookupAsset.mockResolvedValue(mockAssets);
        renderComponent();

        const assetInput = screen.getByLabelText('Asset');
        fireEvent.change(assetInput, { target: { value: 'AAPL' } });

        await waitFor(() => {
            expect(mockLookupAsset).toHaveBeenCalledWith('AAPL');
            expect(screen.getByText('Apple Inc. (AAPL)')).toBeInTheDocument();
        });
    });

    it('allows selecting an asset from search results', async () => {
        mockLookupAsset.mockResolvedValue(mockAssets);
        renderComponent();

        const assetInput = screen.getByLabelText('Asset');
        fireEvent.change(assetInput, { target: { value: 'GOOG' } });

        const searchResult = await screen.findByText('Alphabet Inc. (GOOGL)');
        fireEvent.click(searchResult);

        expect(assetInput).toHaveValue('Alphabet Inc.');
        // Search results should disappear
        expect(screen.queryByText('Apple Inc. (AAPL)')).not.toBeInTheDocument();
    });

    it('submits the form with correct data for an existing asset', async () => {
        mockLookupAsset.mockResolvedValue([mockAssets[0]]);
        renderComponent();

        // Select an asset
        const assetInput = screen.getByLabelText('Asset');
        fireEvent.change(assetInput, { target: { value: 'AAPL' } });
        const searchResult = await screen.findByText('Apple Inc. (AAPL)');
        fireEvent.click(searchResult);

        // Fill form
        fireEvent.change(screen.getByLabelText('Quantity'), { target: { value: '10' } });
        fireEvent.change(screen.getByLabelText('Price per Unit'), { target: { value: '150' } });
        fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2025-07-27' } });

        // Submit
        fireEvent.click(screen.getByRole('button', { name: 'Save Transaction' }));

        await waitFor(() => {

        expect(mockMutateTransaction).toHaveBeenCalledWith(
            {
                portfolioId: 1,
                data: expect.objectContaining({
                    asset_id: 1,
                    quantity: 10,
                    price_per_unit: 150,
                    transaction_type: 'BUY',
                }),
            },
            expect.any(Object)
        );
        });
    });

    it('shows a "Create Asset" button when search returns no results', async () => {
        mockLookupAsset.mockResolvedValue([]);
        renderComponent();

        const assetInput = screen.getByLabelText('Asset');
        fireEvent.change(assetInput, { target: { value: 'NEW' } });

        await waitFor(() => {
            expect(mockLookupAsset).toHaveBeenCalledWith('NEW');
        });

        expect(screen.getByRole('button', { name: 'Create Asset "NEW"' })).toBeInTheDocument();
    });

    it('calls the create asset mutation when the "Create Asset" button is clicked', async () => {
        mockLookupAsset.mockResolvedValue([]);
        renderComponent();

        const assetInput = screen.getByLabelText('Asset');
        fireEvent.change(assetInput, { target: { value: 'NEW' } });

        const createButton = await screen.findByRole('button', { name: 'Create Asset "NEW"' });
        fireEvent.click(createButton);

        expect(mockMutateAsset).toHaveBeenCalledWith('NEW', expect.any(Object));
    });

    it('displays an API error on transaction submission failure', async () => {
        const error = { response: { data: { detail: 'Insufficient funds' } } };
        mockMutateTransaction.mockImplementation((_vars, { onError }) => onError(error));
        mockLookupAsset.mockResolvedValue([mockAssets[0]]);
        renderComponent();

        // Select an asset
        const assetInput = screen.getByLabelText('Asset');
        fireEvent.change(assetInput, { target: { value: 'AAPL' } });
        const searchResult = await screen.findByText('Apple Inc. (AAPL)');
        fireEvent.click(searchResult);

        // Fill and submit
        fireEvent.change(screen.getByLabelText('Quantity'), { target: { value: '10' } });
        fireEvent.change(screen.getByLabelText('Price per Unit'), { target: { value: '150' } });
        fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2025-07-27' } });
        fireEvent.click(screen.getByRole('button', { name: 'Save Transaction' }));

        await waitFor(() => {
            expect(screen.getByText('Insufficient funds')).toBeInTheDocument();
        });
    });
});

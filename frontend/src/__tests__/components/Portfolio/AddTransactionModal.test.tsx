import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import AddTransactionModal from '../../../components/Portfolio/AddTransactionModal';
import * as usePortfoliosHook from '../../../hooks/usePortfolios';
import { Asset } from '../../../types/portfolio';

const queryClient = new QueryClient();
const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockAsset: Asset = { id: 1, ticker_symbol: 'GOOGL', name: 'Alphabet Inc.', asset_type: 'STOCK', currency: 'USD' };

describe('AddTransactionModal', () => {
    const mockOnClose = jest.fn();
    const mockLookupAsset = jest.fn();
    const mockCreateTransaction = jest.fn();

    beforeEach(() => {
        jest.spyOn(usePortfoliosHook, 'useLookupAsset').mockReturnValue({
            mutateAsync: mockLookupAsset,
            isPending: false,
        } as any);
        jest.spyOn(usePortfoliosHook, 'useCreateTransaction').mockReturnValue({
            mutate: mockCreateTransaction,
            isPending: false,
            isSuccess: false,
            isError: false,
            reset: jest.fn(),
        } as any);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('looks up asset on ticker blur and populates fields on success', async () => {
        mockLookupAsset.mockResolvedValue(mockAsset);
        render(<AddTransactionModal isOpen={true} onClose={mockOnClose} portfolioId={1} />, { wrapper });

        const tickerInput = screen.getByLabelText(/ticker symbol/i);
        await userEvent.type(tickerInput, 'GOOGL');
        await userEvent.tab(); // Triggers onBlur

        await waitFor(() => {
            expect(mockLookupAsset).toHaveBeenCalledWith('GOOGL');
            expect(screen.getByLabelText(/asset name/i)).toHaveValue('Alphabet Inc.');
            expect(screen.getByLabelText(/asset type/i)).toHaveValue('STOCK');
            expect(screen.getByLabelText(/currency/i)).toHaveValue('USD');
        });

        // Check that fields are disabled
        expect(screen.getByLabelText(/asset name/i)).toBeDisabled();
    });

    it('enables manual entry when asset lookup fails', async () => {
        mockLookupAsset.mockRejectedValue(new Error('Not Found'));
        render(<AddTransactionModal isOpen={true} onClose={mockOnClose} portfolioId={1} />, { wrapper });

        const tickerInput = screen.getByLabelText(/ticker symbol/i);
        await userEvent.type(tickerInput, 'UNKNOWN');
        await userEvent.tab();

        await waitFor(() => {
            expect(screen.getByText(/asset not found. please enter details manually./i)).toBeInTheDocument();
        });

        const nameInput = screen.getByLabelText(/asset name/i);
        expect(nameInput).toBeEnabled();
        await userEvent.type(nameInput, 'Unknown Company');
        expect(nameInput).toHaveValue('Unknown Company');
    });

    it('submits correct data for a new asset', async () => {
        mockLookupAsset.mockRejectedValue(new Error('Not Found'));
        render(<AddTransactionModal isOpen={true} onClose={mockOnClose} portfolioId={1} />, { wrapper });

        // Manual entry
        await userEvent.type(screen.getByLabelText(/ticker symbol/i), 'MANUAL');
        await userEvent.tab();
        await waitFor(() => expect(screen.getByLabelText(/asset name/i)).toBeEnabled());
        await userEvent.type(screen.getByLabelText(/asset name/i), 'Manual Asset');
        await userEvent.type(screen.getByLabelText(/asset type/i), 'STOCK');
        await userEvent.type(screen.getByLabelText(/currency/i), 'USD');

        // Transaction details
        await userEvent.selectOptions(screen.getByLabelText('Type', { exact: true }), 'BUY');
        await userEvent.type(screen.getByLabelText(/date/i), '2024-01-01');
        await userEvent.type(screen.getByLabelText(/quantity/i), '100');
        await userEvent.type(screen.getByLabelText(/price\/unit/i), '10');

        await userEvent.click(screen.getByRole('button', { name: /add transaction/i }));

        await waitFor(() => {
            expect(mockCreateTransaction).toHaveBeenCalledWith(expect.objectContaining({
                portfolio_id: 1,
                new_asset: {
                    ticker_symbol: 'MANUAL',
                    name: 'Manual Asset',
                    asset_type: 'STOCK',
                    currency: 'USD',
                },
                quantity: 100,
                price_per_unit: 10,
                fees: 0,
                transaction_type: 'BUY',
                transaction_date: '2024-01-01T00:00:00.000Z',
            }));
        });
    });
});
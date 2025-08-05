import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom';
import ImportPreviewPage from '../../../pages/Import/ImportPreviewPage';
import { useImportSession, useParsedTransactions, useCommitImportSession } from '../../../hooks/useImport';

// Mock hooks
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
}));
jest.mock('../../../hooks/useImport');

const mockUseImportSession = useImportSession as jest.Mock;
const mockUseParsedTransactions = useParsedTransactions as jest.Mock;
const mockUseCommitImportSession = useCommitImportSession as jest.Mock;
const mockNavigate = useNavigate as jest.Mock;

const queryClient = new QueryClient();

const renderComponent = (sessionId: string) => {
    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter initialEntries={[`/import/${sessionId}/preview`]}>
                <Routes>
                    <Route path="/import/:sessionId/preview" element={<ImportPreviewPage />} />
                </Routes>
            </MemoryRouter>
        </QueryClientProvider>
    );
};

describe('ImportPreviewPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockNavigate.mockReturnValue(jest.fn());
        mockUseImportSession.mockReturnValue({
            data: {
                id: 'session-123',
                file_name: 'test.csv',
                status: 'PARSED',
                portfolio: { name: 'My Stocks' },
                portfolio_id: 'port-1',
            },
            isLoading: false,
        });
        mockUseParsedTransactions.mockReturnValue({
            data: [
                {
                    transaction_date: '2023-01-01T00:00:00Z',
                    ticker_symbol: 'TEST',
                    transaction_type: 'BUY',
                    quantity: 10,
                    price_per_unit: 100,
                    fees: 5,
                },
            ],
            isLoading: false,
        });
    });

    it('renders the preview table with transaction data', () => {
        mockUseCommitImportSession.mockReturnValue({ isPending: false });
        renderComponent('session-123');

        expect(screen.getByText('Import Preview')).toBeInTheDocument();
        expect(screen.getByText('TEST')).toBeInTheDocument();
        expect(screen.getByText('BUY')).toBeInTheDocument();
        expect(screen.getByText('10')).toBeInTheDocument(); // Quantity
        expect(screen.getByText('₹100.00')).toBeInTheDocument(); // Price
    });

    it('calls the commit mutation when "Commit Transactions" is clicked', () => {
        const mockMutate = jest.fn();
        mockUseCommitImportSession.mockReturnValue({ mutate: mockMutate, isPending: false });

        renderComponent('session-123');

        const commitButton = screen.getByRole('button', { name: 'Commit Transactions' });
        expect(commitButton).toBeEnabled();
        fireEvent.click(commitButton);

        expect(mockMutate).toHaveBeenCalledWith({ sessionId: 'session-123', portfolioId: 'port-1' });
    });

    it('displays a success message and navigates on successful commit', async () => {
        const mockNavigateFn = jest.fn();
        mockNavigate.mockReturnValue(mockNavigateFn);
        mockUseCommitImportSession.mockReturnValue({
            isSuccess: true,
            isPending: false,
            data: { msg: 'Successfully committed 1 transactions.' },
        });
        renderComponent('session-123');

        expect(screen.getByText(/Successfully committed.*Redirecting to portfolio/)).toBeInTheDocument();

        // Check for navigation after delay
        await waitFor(() => {
            expect(mockNavigateFn).toHaveBeenCalledWith('/portfolios/port-1');
        }, { timeout: 2500 });
    });
});

